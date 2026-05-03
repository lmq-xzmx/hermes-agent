"""
Migration 003: Add CapacityAlert Model

添加容量告警数据模型：
- hfm_capacity_alerts (容量告警记录)

执行方式:
    python migrations/003_add_capacity_alerts_model.py

回滚方式:
    python migrations/003_add_capacity_alerts_model.py --rollback
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text


def get_engine():
    """获取数据库引擎"""
    db_path = os.environ.get("HFM_DB_PATH", os.path.expanduser("~/.hermes/file_manager/hfm.db"))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def upgrade(engine):
    """创建容量告警表"""
    print("[Migration] Creating capacity_alerts table...")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hfm_capacity_alerts (
                id VARCHAR(36) PRIMARY KEY,
                type VARCHAR(32) NOT NULL,
                level VARCHAR(16) NOT NULL,
                space_id VARCHAR(36) NOT NULL,
                space_name VARCHAR(64),
                pool_id VARCHAR(36) NOT NULL,
                pool_name VARCHAR(64),
                message TEXT,
                current_usage REAL,
                threshold REAL,
                acknowledged INTEGER DEFAULT 0,
                acknowledged_by VARCHAR(36),
                acknowledged_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (space_id) REFERENCES hfm_spaces(id),
                FOREIGN KEY (pool_id) REFERENCES hfm_storage_pools(id),
                FOREIGN KEY (acknowledged_by) REFERENCES hfm_users(id)
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_capacity_alerts_space
            ON hfm_capacity_alerts(space_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_capacity_alerts_pool
            ON hfm_capacity_alerts(pool_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_capacity_alerts_acknowledged
            ON hfm_capacity_alerts(acknowledged)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_capacity_alerts_created
            ON hfm_capacity_alerts(created_at)
        """))

        conn.commit()

    print("[Migration] capacity_alerts table created successfully")


def downgrade(engine):
    """删除容量告警表"""
    print("[Migration] Dropping capacity_alerts table...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS hfm_capacity_alerts"))
        conn.commit()

    print("[Migration] capacity_alerts table dropped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    engine = get_engine()

    if args.rollback:
        downgrade(engine)
    else:
        upgrade(engine)
