"""
Migration 001: Add Approval Models

添加审批数据模型：
- hfm_approval_requests (资源申请单)
- hfm_approval_records (审批记录)

执行方式:
    python migrations/001_add_approval_models.py

回滚方式:
    python migrations/001_add_approval_models.py --rollback
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text
from engine.models import Base


def get_engine():
    """获取数据库引擎"""
    db_path = os.environ.get("HFM_DB_PATH", "/tmp/hermes_file_manager.db")
    return create_engine(f"sqlite:///{db_path}")


def upgrade(engine):
    """创建审批表"""
    print("[Migration] Creating approval tables...")

    # 创建 hfm_approval_requests 表
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS hfm_approval_requests (
            id VARCHAR(36) PRIMARY KEY,
            type VARCHAR(32) NOT NULL,
            applicant_id VARCHAR(36) NOT NULL,
            target_id VARCHAR(36),
            status VARCHAR(16) DEFAULT 'pending',
            reason TEXT,
            params JSON,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_by VARCHAR(36),
            approved_at DATETIME,
            approval_comment TEXT,
            FOREIGN KEY (applicant_id) REFERENCES hfm_users(id),
            FOREIGN KEY (approved_by) REFERENCES hfm_users(id)
        )
    """))

    # 创建索引
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_approval_request_applicant
        ON hfm_approval_requests(applicant_id)
    """))
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_approval_request_status
        ON hfm_approval_requests(status)
    """))
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_approval_request_type_status
        ON hfm_approval_requests(type, status)
    """))

    # 创建 hfm_approval_records 表
    engine.execute(text("""
        CREATE TABLE IF NOT EXISTS hfm_approval_records (
            id VARCHAR(36) PRIMARY KEY,
            request_id VARCHAR(36) NOT NULL,
            approver_id VARCHAR(36) NOT NULL,
            decision VARCHAR(16) NOT NULL,
            comment TEXT,
            decided_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (request_id) REFERENCES hfm_approval_requests(id),
            FOREIGN KEY (approver_id) REFERENCES hfm_users(id)
        )
    """))

    # 创建索引
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_approval_record_request
        ON hfm_approval_records(request_id)
    """))
    engine.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_approval_record_approver
        ON hfm_approval_records(approver_id)
    """))

    print("[Migration] Approval tables created successfully")


def downgrade(engine):
    """删除审批表"""
    print("[Migration] Dropping approval tables...")

    engine.execute(text("DROP TABLE IF EXISTS hfm_approval_records"))
    engine.execute(text("DROP TABLE IF EXISTS hfm_approval_requests"))

    print("[Migration] Approval tables dropped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    engine = get_engine()

    if args.rollback:
        downgrade(engine)
    else:
        upgrade(engine)
