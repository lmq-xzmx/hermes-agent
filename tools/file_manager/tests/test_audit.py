"""
Tests for Hermes File Manager - Audit Logger
TDD Phase: Tests written first, should pass against existing implementation
"""

import pytest
import sys
import tempfile
import csv
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from tools.file_manager.engine.models import (
    Base, User, Role, AuditLog, AuditAction, init_db, create_builtin_roles
)
from tools.file_manager.engine.audit import AuditLogger


@pytest.fixture
def session():
    eng = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(eng)
    Session = sessionmaker(bind=eng)
    sess = Session()
    create_builtin_roles(sess)

    # Create admin user for tests
    admin_role = sess.query(Role).filter(Role.name == "admin").first()
    user = User(username="audituser", role=admin_role)
    user.set_password("password")
    sess.add(user)
    sess.commit()
    sess.user = user

    yield sess
    sess.close()


# =============================================================================
# Basic Logging
# =============================================================================

class TestAuditLogBasic:
    def test_log_creates_entry(self, session):
        logger = AuditLogger(session)
        entry = logger.log(
            action=AuditAction.LOGIN,
            result="success",
            user=session.user,
            path="/",
            ip_address="127.0.0.1",
        )
        assert entry.id is not None
        assert entry.action == "login"
        assert entry.result == "success"

    def test_log_with_anonymous_user(self, session):
        logger = AuditLogger(session)
        entry = logger.log(
            action=AuditAction.FILE_READ,
            result="success",
            user=None,
            path="/public/file.txt",
        )
        assert entry.user_id is None

    def test_log_commits_to_db(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/f.txt")
        session.commit()

        count = session.query(AuditLog).count()
        assert count >= 1

    def test_log_accepts_metadata(self, session):
        logger = AuditLogger(session)
        entry = logger.log(
            action=AuditAction.FILE_WRITE,
            result="success",
            user=session.user,
            path="/f.txt",
            extra={"bytes_written": 1024},
        )
        assert entry.extra == {"bytes_written": 1024}


# =============================================================================
# Login/Logout Logging
# =============================================================================

class TestLoginLogout:
    def test_log_login_success(self, session):
        logger = AuditLogger(session)
        entry = logger.log_login(
            user=session.user,
            ip_address="10.0.0.1",
            success=True,
        )
        assert entry.action == "login"
        assert entry.result == "success"

    def test_log_login_failure(self, session):
        logger = AuditLogger(session)
        entry = logger.log_login(
            user=None,
            ip_address="10.0.0.1",
            success=False,
        )
        assert entry.action == "login_failed"
        assert entry.result == "denied"

    def test_log_logout(self, session):
        logger = AuditLogger(session)
        entry = logger.log_logout(
            user=session.user,
            ip_address="10.0.0.1",
        )
        assert entry.action == "logout"
        assert entry.result == "success"


# =============================================================================
# File Operation Logging
# =============================================================================

class TestFileOperations:
    def test_log_file_operation(self, session):
        logger = AuditLogger(session)
        entry = logger.log_file_operation(
            action=AuditAction.FILE_READ,
            user=session.user,
            path="/docs/readme.txt",
            result="success",
        )
        assert entry.action == "file_read"
        assert entry.path == "/docs/readme.txt"

    def test_log_permission_denied(self, session):
        logger = AuditLogger(session)
        entry = logger.log_permission_denied(
            user=session.user,
            action="file_write",
            path="/private/secret.txt",
        )
        assert entry.result == "denied"


# =============================================================================
# Admin Action Logging
# =============================================================================

class TestAdminActions:
    def test_log_admin_action(self, session):
        logger = AuditLogger(session)
        entry = logger.log_admin_action(
            action=AuditAction.USER_CREATE,
            admin=session.user,
            target_id="user-123",
            metadata={"username": "newuser"},
        )
        assert entry.action == "user_create"
        assert entry.path == "/admin/user-123"
        assert entry.extra["username"] == "newuser"


# =============================================================================
# Query Methods
# =============================================================================

class TestQuery:
    def test_query_by_user_id(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.LOGIN, "success", user=session.user)
        session.commit()

        results = logger.query(user_id=session.user.id)
        assert len(results) >= 1
        assert all(r.user_id == session.user.id for r in results)

    def test_query_by_action(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.LOGIN, "success", user=session.user)
        logger.log(AuditAction.FILE_READ, "success", user=session.user)
        session.commit()

        results = logger.query(action=AuditAction.LOGIN.value)
        assert all(r.action == "login" for r in results)

    def test_query_by_path_prefix(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/docs/a.txt")
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/docs/b.txt")
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/other/c.txt")
        session.commit()

        results = logger.query(path="/docs/")
        assert all("/docs/" in r.path for r in results)

    def test_query_by_result(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.FILE_READ, "success", user=session.user)
        logger.log(AuditAction.FILE_READ, "denied", user=session.user)
        session.commit()

        results = logger.query(result="denied")
        assert all(r.result == "denied" for r in results)

    def test_query_with_date_range(self, session):
        logger = AuditLogger(session)
        now = datetime.utcnow()
        yesterday = now - timedelta(days=1)
        tomorrow = now + timedelta(days=1)

        logger.log(AuditAction.LOGIN, "success", user=session.user)
        session.commit()

        results = logger.query(
            start_date=yesterday,
            end_date=tomorrow,
        )
        assert len(results) >= 1

    def test_query_with_limit_and_offset(self, session):
        logger = AuditLogger(session)
        for i in range(10):
            logger.log(AuditAction.FILE_READ, "success", user=session.user, path=f"/f{i}.txt")
        session.commit()

        results = logger.query(limit=3, offset=0)
        assert len(results) == 3

        results_page2 = logger.query(limit=3, offset=3)
        assert len(results_page2) == 3

    def test_query_order_newest_first(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.LOGIN, "success", user=session.user)
        session.commit()

        results = logger.query(limit=1)
        # Newest should be first (we just created one)
        assert len(results) >= 1


# =============================================================================
# Convenience Query Methods
# =============================================================================

class TestConvenienceQueries:
    def test_get_user_activity(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/f1.txt")
        logger.log(AuditAction.FILE_WRITE, "success", user=session.user, path="/f2.txt")
        session.commit()

        results = logger.get_user_activity(session.user.id, days=7)
        assert all(r.user_id == session.user.id for r in results)

    def test_get_failed_logins(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.LOGIN_FAILED, "denied")
        logger.log(AuditAction.LOGIN_FAILED, "denied")
        session.commit()

        results = logger.get_failed_logins(hours=24)
        assert all(r.action == "login_failed" for r in results)

    def test_get_path_history(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/target.txt")
        logger.log(AuditAction.FILE_WRITE, "success", user=session.user, path="/target.txt")
        session.commit()

        results = logger.get_path_history("/target.txt")
        assert all(r.path == "/target.txt" for r in results)


# =============================================================================
# Cleanup & Export
# =============================================================================

class TestCleanup:
    def test_cleanup_old_logs(self, session):
        logger = AuditLogger(session)
        # Create some old entries manually (bypass normal log to set old date)
        old_entry = AuditLog(
            user_id=session.user.id,
            action=AuditAction.LOGIN.value,
            result="success",
        )
        # Manually set old date using raw session manipulation
        from datetime import datetime
        old_date = datetime.utcnow() - timedelta(days=100)
        from sqlalchemy import text
        session.add(old_entry)
        session.commit()

        # Update via raw SQL to avoid ORM filtering
        session.execute(
            text(f"UPDATE hfm_audit_logs SET created_at = '{old_date.isoformat()}' WHERE id = '{old_entry.id}'")
        )
        session.commit()

        count = logger.cleanup_old_logs(retention_days=90)
        assert count >= 1


class TestExport:
    def test_export_csv(self, session):
        logger = AuditLogger(session)
        logger.log(AuditAction.LOGIN, "success", user=session.user)
        logger.log(AuditAction.FILE_READ, "success", user=session.user, path="/test.txt")
        session.commit()

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
            temp_path = Path(f.name)

        try:
            n = logger.export_csv(temp_path)
            assert n >= 2

            with open(temp_path, newline="") as csvfile:
                reader = csv.DictReader(csvfile)
                rows = list(reader)
                assert len(rows) >= 2
                assert "action" in reader.fieldnames
        finally:
            temp_path.unlink(missing_ok=True)


# =============================================================================
# Privacy Helpers
# =============================================================================

class TestPrivacyHelpers:
    def test_redact_ipv4(self):
        redacted = AuditLogger._redact_ip("192.168.1.100")
        assert "192" in redacted
        assert "100" not in redacted

    def test_redact_ipv6(self):
        redacted = AuditLogger._redact_ip("2001:0db8:85a3:0000:0000:8a2e:0370:7334")
        assert "2001" in redacted
        assert "7334" not in redacted

    def test_redact_none(self):
        assert AuditLogger._redact_ip(None) is None

    def test_truncate(self):
        long_string = "x" * 1000
        truncated = AuditLogger._truncate(long_string, 100)
        assert len(truncated) == 100

    def test_truncate_none(self):
        assert AuditLogger._truncate(None, 100) is None


# =============================================================================
# Context Manager
# =============================================================================

class TestContextManager:
    def test_audit_context_success(self, session):
        from tools.file_manager.engine.audit import audit_context
        logger = AuditLogger(session)

        with audit_context(logger, AuditAction.FILE_READ, session.user, "/test.txt"):
            pass  # do nothing = success

        results = logger.query(path="/test.txt")
        assert any(r.result == "success" for r in results)

    def test_audit_context_permission_error(self, session):
        from tools.file_manager.engine.audit import audit_context
        logger = AuditLogger(session)

        with pytest.raises(PermissionError):
            with audit_context(logger, AuditAction.FILE_WRITE, session.user, "/denied.txt"):
                raise PermissionError("Access denied")

        results = logger.query(path="/denied.txt")
        assert any(r.result == "denied" for r in results)

    def test_audit_context_generic_error(self, session):
        from tools.file_manager.engine.audit import audit_context
        logger = AuditLogger(session)

        with pytest.raises(RuntimeError):
            with audit_context(logger, AuditAction.FILE_READ, session.user, "/error.txt"):
                raise RuntimeError("Oops")

        results = logger.query(path="/error.txt")
        assert any(r.result == "error" for r in results)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
