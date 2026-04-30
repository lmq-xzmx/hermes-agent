"""
Tests for TeamService and storage pool management.
"""

import pytest
import sys
from pathlib import Path
from datetime import datetime, timedelta

# Make file_manager importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.engine.models import init_db, Base, StoragePool, Team, TeamMember, TeamCredential, User


@pytest.fixture
def db_session(tmp_path, monkeypatch):
    """Create an in-memory SQLite DB with all tables."""
    # Point HOME to temp dir so ~/.hermes doesn't interfere
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setenv("HERMES_HOME", str(tmp_path / ".hermes"))

    from tools.file_manager.engine.models import init_db
    factory = init_db("sqlite:///:memory:")
    session = factory()
    # Seed a test user
    from tools.file_manager.engine.models import User, Role
    user = User(username="alice", email="alice@test.local")
    user.set_password("secret123")
    session.add(user)
    admin_role = Role(name="admin", description="Admin")
    session.add(admin_role)
    session.commit()
    return session


@pytest.fixture
def team_service(db_session):
    from tools.file_manager.services.team_service import TeamService
    # TeamService needs a db_factory
    class FakeFactory:
        def __call__(self):
            return db_session
    return TeamService(db_factory=FakeFactory())


class TestStoragePoolModel:
    def test_create_pool(self, db_session):
        pool = StoragePool(
            name="Test Pool",
            base_path="/tmp/test-pool",
            protocol="local",
            total_bytes=10 * 1024**3,
        )
        db_session.add(pool)
        db_session.commit()
        assert pool.id is not None
        assert pool.is_active is True
        assert pool.protocol == "local"

    def test_pool_to_dict(self, db_session):
        pool = StoragePool(name="Dict Pool", base_path="/tmp/dict", protocol="local")
        db_session.add(pool)
        db_session.commit()
        d = pool.to_dict()
        assert d["name"] == "Dict Pool"
        assert d["protocol"] == "local"
        assert d["is_active"] is True


class TestTeamModel:
    def test_create_team(self, db_session, tmp_path):
        pool = StoragePool(name="Pool", base_path=str(tmp_path / "pool"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()

        team = Team(
            name="Alpha Team",
            storage_pool_id=pool.id,
            max_bytes=5 * 1024**3,
            owner_id=user.id,
        )
        db_session.add(team)
        db_session.commit()

        assert team.id is not None
        assert team.is_active is True
        assert team.used_bytes == 0

    def test_team_to_dict(self, db_session, tmp_path):
        pool = StoragePool(name="Pool2", base_path=str(tmp_path / "p2"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()

        team = Team(name="Dict Team", storage_pool_id=pool.id, owner_id=user.id, max_bytes=1000)
        db_session.add(team)
        db_session.commit()

        d = team.to_dict()
        assert d["name"] == "Dict Team"
        assert d["max_bytes"] == 1000
        assert d["used_bytes"] == 0
        assert d["is_active"] is True


class TestTeamMemberModel:
    def test_member_role(self, db_session, tmp_path):
        pool = StoragePool(name="Pool3", base_path=str(tmp_path / "p3"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()
        team = Team(name="Member Test", storage_pool_id=pool.id, owner_id=user.id)
        db_session.add(team)
        db_session.commit()

        member = TeamMember(team_id=team.id, user_id=user.id, role="owner")
        db_session.add(member)
        db_session.commit()

        assert member.role == "owner"
        d = member.to_dict()
        assert d["role"] == "owner"
        assert d["username"] == "alice"


class TestTeamCredentialModel:
    def test_credential_valid(self, db_session, tmp_path):
        pool = StoragePool(name="Pool4", base_path=str(tmp_path / "p4"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()
        team = Team(name="Cred Test", storage_pool_id=pool.id, owner_id=user.id)
        db_session.add(team)
        db_session.commit()

        cred = TeamCredential(
            team_id=team.id,
            token="abc123token",
            max_uses=5,
            created_by=user.id,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is True
        assert cred.used_count == 0

    def test_credential_expired(self, db_session, tmp_path):
        pool = StoragePool(name="Pool5", base_path=str(tmp_path / "p5"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()
        team = Team(name="Expiry Test", storage_pool_id=pool.id, owner_id=user.id)
        db_session.add(team)
        db_session.commit()

        cred = TeamCredential(
            team_id=team.id,
            token="expired123",
            max_uses=None,
            expires_at=datetime.utcnow() - timedelta(hours=1),
            created_by=user.id,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is False

    def test_credential_max_uses_reached(self, db_session, tmp_path):
        pool = StoragePool(name="Pool6", base_path=str(tmp_path / "p6"), protocol="local")
        db_session.add(pool)
        db_session.commit()

        from tools.file_manager.engine.models import User
        user = db_session.query(User).first()
        team = Team(name="Max Uses Test", storage_pool_id=pool.id, owner_id=user.id)
        db_session.add(team)
        db_session.commit()

        cred = TeamCredential(
            team_id=team.id,
            token="maxuses123",
            max_uses=2,
            used_count=2,
            created_by=user.id,
        )
        db_session.add(cred)
        db_session.commit()

        assert cred.is_valid() is False


class TestTeamService:
    def test_ensure_default_pool_creates_pool(self, team_service):
        team_service.ensure_default_pool()
        pools = team_service.list_pools()
        assert len(pools) >= 1
        assert any(p["name"] == "本地存储（默认）" for p in pools)

    def test_create_pool(self, team_service, tmp_path):
        pool = team_service.create_pool(
            name="My Pool",
            base_path=str(tmp_path / "my-pool"),
            protocol="local",
        )
        assert pool["name"] == "My Pool"
        assert pool["protocol"] == "local"

    def test_create_and_list_team(self, team_service, tmp_path):
        pool = team_service.create_pool(
            name="Team Pool", base_path=str(tmp_path / "tpool"), protocol="local"
        )
        # Get user id from db
        from tools.file_manager.engine.models import User
        session = team_service._db()
        user = session.query(User).first()
        team = team_service.create_team(
            name="Platform Team",
            owner_id=user.id,
            storage_pool_id=pool["id"],
            max_bytes=1024 * 1024,
        )
        assert team["name"] == "Platform Team"

        teams = team_service.list_teams()
        assert any(t["name"] == "Platform Team" for t in teams)

    def test_join_team_via_credential(self, team_service, tmp_path):
        pool = team_service.create_pool(
            name="Join Pool", base_path=str(tmp_path / "jpool"), protocol="local"
        )
        # Get owner id
        from tools.file_manager.engine.models import User
        session = team_service._db()
        owner = session.query(User).first()
        team = team_service.create_team(
            name="Joinable Team",
            owner_id=owner.id,
            storage_pool_id=pool["id"],
            max_bytes=0,
        )
        cred = team_service.create_credential(
            team_id=team["id"],
            created_by=owner.id,
            max_uses=None,
            expires_at=None,
        )
        assert cred["token"] is not None

        # Join as a new user
        from tools.file_manager.engine.models import User
        session = team_service._db()
        bob = User(username="bob", email="bob@test.local")
        bob.set_password("secret456")
        session.add(bob)
        session.commit()

        result = team_service.join_via_credential(token=cred["token"], user_id=bob.id)
        assert result["name"] == "Joinable Team"

    def test_quota_enforcement(self, team_service, tmp_path):
        pool = team_service.create_pool(
            name="Quota Pool", base_path=str(tmp_path / "qpool"), protocol="local"
        )
        # Get owner id
        from tools.file_manager.engine.models import User
        session = team_service._db()
        owner = session.query(User).first()
        team = team_service.create_team(
            name="Small Quota",
            owner_id=owner.id,
            storage_pool_id=pool["id"],
            max_bytes=100,
        )
        from tools.file_manager.services.team_service import TeamQuotaExceeded
        with pytest.raises(TeamQuotaExceeded) as exc_info:
            team_service.check_quota_for_write(
                team_id=team["id"],
                content_size=200,
            )
        assert exc_info.value.max_bytes == 100


class TestStorageAdapters:
    def test_local_adapter_basic(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import LocalStorageAdapter

        adapter = LocalStorageAdapter(str(tmp_path / "local_test"))
        # Root always exists (created by __init__)
        assert adapter.exists("/") is True
        assert adapter.is_dir("/") is True

        # Write a file
        adapter.write_file("/hello.txt", b"world")
        assert adapter.exists("/hello.txt") is True
        assert adapter.is_file("/hello.txt") is True
        assert adapter.is_dir("/hello.txt") is False
        assert adapter.read_file("/hello.txt") == b"world"

        # Make dir and list
        adapter.mkdir("/subdir")
        assert adapter.is_dir("/subdir") is True
        assert "hello.txt" in adapter.list_dir("/")

        # Delete
        adapter.delete("/hello.txt")
        assert adapter.exists("/hello.txt") is False

        # Stat
        st = adapter.stat("/subdir")
        assert st["type"] == "directory"

        # Space
        assert adapter.get_free_space() > 0
        assert adapter.get_total_space() > 0

    def test_local_adapter_path_escape_blocked(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import LocalStorageAdapter

        adapter = LocalStorageAdapter(str(tmp_path / "escape_test"))
        # Writing outside root should fail at path resolution
        with pytest.raises(ValueError, match="Path escape"):
            adapter._resolve("../etc/passwd")
        
        # Also test that we can write inside our root
        adapter.write_file("/safe.txt", b"ok")
        assert adapter.exists("/safe.txt") is True

    def test_factory_local(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        adapter = create_storage_adapter(
            protocol="local",
            base_path=str(tmp_path / "factory_test"),
        )
        assert adapter is not None
        # Verify it works
        assert adapter.exists("/") is True

    def test_factory_unknown_protocol(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        with pytest.raises(ValueError, match="Unknown storage protocol"):
            create_storage_adapter(
                protocol="ftp",
                base_path="/tmp/data",
            )

    def test_factory_smb_missing_host(self):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        with pytest.raises(ValueError, match="host/share"):
            create_storage_adapter(
                protocol="smb",
                base_path="/ambiguous/path",
            )

    def test_factory_s3_requires_boto3(self, tmp_path):
        from tools.file_manager.engine.storage_adapters import create_storage_adapter

        # If boto3 is installed this test is moot, skip it
        try:
            import boto3
            pytest.skip("boto3 is installed, test not applicable")
        except ImportError:
            pass

        # Should raise about missing boto3
        with pytest.raises(RuntimeError, match="boto3"):
            create_storage_adapter(
                protocol="s3",
                base_path="my-bucket",
                endpoint="s3.amazonaws.com",
            )
