"""
Migration 002: Add QuotaTransfer Model

添加配额调配数据模型：
- hfm_quota_transfers (配额调配记录)

执行方式:
    python migrations/002_add_quota_transfer_model.py

回滚方式:
    python migrations/002_add_quota_transfer_model.py --rollback
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import create_engine, text


def get_engine():
    """获取数据库引擎"""
    db_path = os.environ.get("HFM_DB_PATH", os.path.expanduser("~/.hermes/file_manager/hfm.db"))
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    return create_engine(f"sqlite:///{db_path}")


def upgrade(engine):
    """创建配额调配表"""
    print("[Migration] Creating quota_transfer table...")

    with engine.connect() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS hfm_quota_transfers (
                id VARCHAR(36) PRIMARY KEY,
                from_space_id VARCHAR(36) NOT NULL,
                to_space_id VARCHAR(36) NOT NULL,
                transfer_bytes BIGINT NOT NULL,
                reason TEXT,
                requested_by VARCHAR(36) NOT NULL,
                approved_by VARCHAR(36),
                status VARCHAR(16) DEFAULT 'pending',
                rejection_reason TEXT,
                expires_at DATETIME NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (from_space_id) REFERENCES hfm_spaces(id),
                FOREIGN KEY (to_space_id) REFERENCES hfm_spaces(id),
                FOREIGN KEY (requested_by) REFERENCES hfm_users(id),
                FOREIGN KEY (approved_by) REFERENCES hfm_users(id)
            )
        """))

        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_quota_transfers_status
            ON hfm_quota_transfers(status)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_quota_transfers_from
            ON hfm_quota_transfers(from_space_id)
        """))
        conn.execute(text("""
            CREATE INDEX IF NOT EXISTS ix_quota_transfers_to
            ON hfm_quota_transfers(to_space_id)
        """))

        conn.commit()

    print("[Migration] quota_transfer table created successfully")


def downgrade(engine):
    """删除配额调配表"""
    print("[Migration] Dropping quota_transfer table...")

    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS hfm_quota_transfers"))
        conn.commit()

    print("[Migration] quota_transfer table dropped")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--rollback", action="store_true")
    args = parser.parse_args()

    engine = get_engine()

    if args.rollback:
        downgrade(engine)
    else:
        upgrade(engine)
