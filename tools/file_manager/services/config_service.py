"""
ConfigService - 配置管理服务

提供配置加载、持久化、版本管理、变更审计等功能。
"""

from __future__ import annotations

import os
import uuid
import yaml
from datetime import datetime
from typing import Dict, Any, Optional, Callable
from pathlib import Path
from dataclasses import dataclass, field

from sqlalchemy.orm import Session


@dataclass
class ConfigChange:
    """配置变更记录"""
    id: str
    key: str
    old_value: Any
    new_value: Any
    changed_by: str
    changed_at: datetime
    reason: Optional[str] = None


@dataclass
class AppConfig:
    """应用配置"""
    storage_pool: Dict[str, Any] = field(default_factory=dict)
    quota: Dict[str, Any] = field(default_factory=dict)
    alert: Dict[str, Any] = field(default_factory=dict)
    billing: Dict[str, Any] = field(default_factory=dict)
    plans: Dict[str, Any] = field(default_factory=dict)


class ConfigService:
    """
    配置管理服务

    支持：
    - 从 YAML 文件加载配置
    - 配置持久化到数据库
    - 配置变更审计
    - 配置热更新
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".hermes" / "file_manager" / "config.yaml"

    def __init__(self, db_factory=None, config_path: str = None):
        self._db = db_factory
        self._config_path = Path(config_path) if config_path else self.DEFAULT_CONFIG_PATH
        self._config: AppConfig = AppConfig()
        self._version = 1
        self._listeners: list = []

        # 加载配置
        self._load_config()

    def _load_config(self) -> None:
        """从文件加载配置"""
        if self._config_path.exists():
            with open(self._config_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f) or {}

            self._config = AppConfig(
                storage_pool=data.get("storage_pool", {}),
                quota=data.get("quota", {}),
                alert=data.get("alert", {}),
                billing=data.get("billing", {}),
                plans=data.get("plans", {}),
            )
        else:
            self._config = self._get_default_config()

    def _get_default_config(self) -> AppConfig:
        """获取默认配置"""
        return AppConfig(
            storage_pool={
                "total_bytes": 2147483648000,  # 2TB
                "reserved_bytes": 536870912000,  # 500GB
                "allow_overcommit": True,
                "soft_warning_ratio": 0.8,
                "hard_block_ratio": 1.0,
                "buffer_ratio": 0.1,
            },
            quota={
                "team_default_quota": 104857600,  # 100MB
                "team_max_quota": 10737418240000,  # 10TB
                "personal_default_quota": 10737418240,  # 10GB
                "personal_max_quota": 107374182400,  # 100GB
                "transferable": True,
                "transfer_max_duration_days": 30,
            },
            alert={
                "enabled": True,
                "check_interval": 300,
                "channels": ["in_app"],
                "thresholds": {
                    "soft_warning": 0.8,
                    "hard_warning": 0.95,
                    "critical": 1.0,
                },
            },
            billing={
                "enabled": False,
                "currency": "CNY",
                "overage_rate": 0.1,
            },
            plans={},
        )

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键，支持点号分隔，如 "storage_pool.total_bytes"
            default: 默认值

        Returns:
            配置值
        """
        parts = key.split(".")
        value = self._config

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return default

            if value is None:
                return default

        return value

    def set(self, key: str, value: Any, changed_by: str = "system", reason: str = None) -> bool:
        """
        设置配置值（仅内存）

        Args:
            key: 配置键
            value: 配置值
            changed_by: 变更人
            reason: 变更原因

        Returns:
            是否成功
        """
        old_value = self.get(key)
        parts = key.split(".")

        # 更新嵌套字典
        target = self._config
        for part in parts[:-1]:
            if part not in target:
                target[part] = {}
            target = target[part]

        target[parts[-1]] = value

        # 记录变更
        change = ConfigChange(
            id=str(uuid.uuid4()),
            key=key,
            old_value=old_value,
            new_value=value,
            changed_by=changed_by,
            changed_at=datetime.utcnow(),
            reason=reason,
        )

        # 通知监听器
        self._notify_change(change)

        return True

    def save_to_file(self) -> bool:
        """
        保存配置到文件

        Returns:
            是否成功
        """
        try:
            self._config_path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "storage_pool": self._config.storage_pool,
                "quota": self._config.quota,
                "alert": self._config.alert,
                "billing": self._config.billing,
                "plans": self._config.plans,
            }

            with open(self._config_path, 'w', encoding='utf-8') as f:
                yaml.dump(data, f, allow_unicode=True, default_flow_style=False)

            return True
        except Exception as e:
            print(f"Failed to save config: {e}")
            return False

    def save_to_db(self, changed_by: str = "system") -> bool:
        """
        保存配置到数据库

        Args:
            changed_by: 变更人

        Returns:
            是否成功
        """
        if not self._db:
            return False

        session = self._get_session()
        try:
            config_json = {
                "storage_pool": self._config.storage_pool,
                "quota": self._config.quota,
                "alert": self._config.alert,
                "billing": self._config.billing,
                "plans": self._config.plans,
            }

            # 保存或更新配置记录
            import json
            config_str = json.dumps(config_json)

            # 简化的实现，实际应该查询并更新
            session.execute(
                f"INSERT OR REPLACE INTO hfm_system_config "
                f"(key, value, version, updated_at, updated_by) "
                f"VALUES ('resource_config', ?, ?, ?, ?)",
                [config_str, self._version, datetime.utcnow().isoformat(), changed_by]
            )

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Failed to save config to DB: {e}")
            return False
        finally:
            session.close()

    def load_from_db(self) -> bool:
        """
        从数据库加载配置

        Returns:
            是否成功
        """
        if not self._db:
            return False

        session = self._get_session()
        try:
            result = session.execute(
                f"SELECT value FROM hfm_system_config WHERE key = 'resource_config'"
            ).fetchone()

            if result:
                import json
                data = json.loads(result["value"])

                self._config = AppConfig(
                    storage_pool=data.get("storage_pool", {}),
                    quota=data.get("quota", {}),
                    alert=data.get("alert", {}),
                    billing=data.get("billing", {}),
                    plans=data.get("plans", {}),
                )
                return True
            return False
        except Exception as e:
            print(f"Failed to load config from DB: {e}")
            return False
        finally:
            session.close()

    def get_change_history(self, limit: int = 50) -> list:
        """
        获取配置变更历史

        Args:
            limit: 返回数量限制

        Returns:
            变更历史列表
        """
        # 简化实现
        return []

    def add_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """
        添加配置变更监听器

        Args:
            listener: 监听器函数
        """
        self._listeners.append(listener)

    def remove_listener(self, listener: Callable[[ConfigChange], None]) -> None:
        """
        移除配置变更监听器

        Args:
            listener: 监听器函数
        """
        if listener in self._listeners:
            self._listeners.remove(listener)

    def _notify_change(self, change: ConfigChange) -> None:
        """通知所有监听器"""
        for listener in self._listeners:
            try:
                listener(change)
            except Exception as e:
                print(f"Config listener error: {e}")

    def _get_session(self) -> Session:
        if callable(self._db):
            return self._db()
        return self._db

    def get_all(self) -> Dict[str, Any]:
        """获取所有配置"""
        return {
            "storage_pool": self._config.storage_pool,
            "quota": self._config.quota,
            "alert": self._config.alert,
            "billing": self._config.billing,
            "plans": self._config.plans,
        }

    def reload(self) -> None:
        """重新加载配置"""
        self._load_config()


# Module exports
__all__ = [
    "ConfigService",
    "AppConfig",
    "ConfigChange",
]
