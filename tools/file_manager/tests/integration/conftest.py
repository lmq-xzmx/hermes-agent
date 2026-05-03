"""
Pytest fixtures for integration tests.

Provides reusable test fixtures for:
- Database sessions
- Test users
- Test spaces
- API clients
- Lifecycle engine context

Uses file-based SQLite for test isolation - each test gets its own database.
"""

import pytest
import sys
from pathlib import Path

# Add tools/ to path so `from file_manager...` imports work
# This conftest is at tests/integration/, so we go up 3 levels to tools/
tools_path = Path(__file__).parent.parent.parent
if str(tools_path) not in sys.path:
    sys.path.insert(0, str(tools_path))


# ============================================================================
# Database Fixtures (function-scoped for test isolation)
# ============================================================================

@pytest.fixture
def db_engine(tmp_path):
    """
    Create a function-scoped SQLite engine pointing to a temp file.
    Each test gets its own database file.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from file_manager.engine.models import Base

    db_path = tmp_path / "test.db"
    database_url = f"sqlite:///{db_path}"

    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )

    Base.metadata.create_all(bind=engine)

    yield engine

    engine.dispose()


@pytest.fixture
def db_session(db_engine):
    """Create a session for each test."""
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
    session = SessionLocal()
    yield session
    session.close()


@pytest.fixture
def db_factory(db_session):
    """Factory that returns the same session."""
    class Factory:
        def __call__(self):
            return db_session
    return Factory()


# ============================================================================
# Environment Fixtures
# ============================================================================

@pytest.fixture
def tmp_hermes_home(tmp_path, monkeypatch):
    """Create a temporary HERMES_HOME for tests."""
    hermes_home = tmp_path / ".hermes"
    hermes_home.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HERMES_HOME", str(hermes_home))
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return hermes_home


# ============================================================================
# User Fixtures
# ============================================================================

@pytest.fixture
def user_role(db_session):
    """Create or get a user role."""
    from file_manager.engine.models import Role

    role = db_session.query(Role).filter(Role.name == "user").first()
    if not role:
        role = Role(name="user", description="Regular user role", is_system=True)
        db_session.add(role)
        db_session.commit()
    return role


@pytest.fixture
def admin_role(db_session):
    """Create or get an admin role."""
    from file_manager.engine.models import Role

    role = db_session.query(Role).filter(Role.name == "admin").first()
    if not role:
        role = Role(name="admin", description="Admin role", is_system=True)
        db_session.add(role)
        db_session.commit()
    return role


@pytest.fixture
def test_user(db_session, user_role):
    """Create a test user (alice)."""
    from file_manager.engine.models import User

    user = User(
        username="alice",
        email="alice@test.local",
        role_id=user_role.id
    )
    user.set_password("secret123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def admin_user(db_session, admin_role):
    """Create an admin user."""
    from file_manager.engine.models import User

    user = User(
        username="admin",
        email="admin@test.local",
        role_id=admin_role.id
    )
    user.set_password("admin123")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture
def test_user_2(db_session, user_role):
    """Create a second test user (bob)."""
    from file_manager.engine.models import User

    user = User(
        username="bob",
        email="bob@test.local",
        role_id=user_role.id
    )
    user.set_password("secret456")
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


# ============================================================================
# Storage Pool Fixtures
# ============================================================================

@pytest.fixture
def storage_pool(db_session):
    """Create a test storage pool (10GB)."""
    from file_manager.engine.models import StoragePool

    pool = StoragePool(
        name="Test Pool",
        base_path="/tmp/test-pool",
        protocol="local",
        total_bytes=10 * 1024**3,  # 10 GB
        free_bytes=10 * 1024**3,
        is_active=True,
    )
    db_session.add(pool)
    db_session.commit()
    db_session.refresh(pool)
    return pool


@pytest.fixture
def small_pool(db_session):
    """Create a small storage pool (1MB) for quota tests."""
    from file_manager.engine.models import StoragePool

    pool = StoragePool(
        name="Small Pool",
        base_path="/tmp/small-pool",
        protocol="local",
        total_bytes=1024**2,  # 1 MB
        free_bytes=1024**2,
        is_active=True,
    )
    db_session.add(pool)
    db_session.commit()
    db_session.refresh(pool)
    return pool


# ============================================================================
# Team Fixtures
# ============================================================================

@pytest.fixture
def team(db_session, test_user, storage_pool):
    """Create a test team with test_user as owner."""
    from file_manager.engine.models import Team

    team = Team(
        name="Test Team",
        owner_id=test_user.id,
        storage_pool_id=storage_pool.id,
        max_bytes=5 * 1024**3,  # 5 GB
        used_bytes=0,
        status="active",
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


@pytest.fixture
def team_2(db_session, test_user_2, storage_pool):
    """Create a second test team."""
    from file_manager.engine.models import Team

    team = Team(
        name="Test Team 2",
        owner_id=test_user_2.id,
        storage_pool_id=storage_pool.id,
        max_bytes=5 * 1024**3,
        used_bytes=0,
        status="active",
    )
    db_session.add(team)
    db_session.commit()
    db_session.refresh(team)
    return team


# ============================================================================
# Space Fixtures
# ============================================================================

@pytest.fixture
def space(db_session, test_user, storage_pool):
    """Create a test space with test_user as owner."""
    from file_manager.engine.models import Space

    space = Space(
        name="Test Space",
        storage_pool_id=storage_pool.id,
        owner_id=test_user.id,
        max_bytes=1 * 1024**3,  # 1 GB
        used_bytes=0,
        space_type="team",
        status="active",
    )
    db_session.add(space)
    db_session.commit()
    db_session.refresh(space)
    return space


@pytest.fixture
def small_space(db_session, test_user, storage_pool):
    """Create a small space (1MB) for quota tests."""
    from file_manager.engine.models import Space

    space = Space(
        name="Small Space",
        storage_pool_id=storage_pool.id,
        owner_id=test_user.id,
        max_bytes=1024**2,  # 1 MB
        used_bytes=0,
        space_type="team",
        status="active",
    )
    db_session.add(space)
    db_session.commit()
    db_session.refresh(space)
    return space


# ============================================================================
# Space Member Fixtures
# ============================================================================

@pytest.fixture
def space_member(db_session, space, test_user):
    """Add test_user as member to space."""
    from file_manager.engine.models import SpaceMember

    member = SpaceMember(
        space_id=space.id,
        user_id=test_user.id,
        role="member",
        status="active",
    )
    db_session.add(member)
    db_session.commit()
    db_session.refresh(member)
    return member


# ============================================================================
# Team Credential Fixtures
# ============================================================================

@pytest.fixture
def team_credential(db_session, team):
    """Create a team invite credential."""
    from file_manager.engine.models import TeamCredential

    cred = TeamCredential(
        team_id=team.id,
        credential="test-token-123",
        created_by=team.owner_id,
        expires_at=None,
        max_uses=None,
        use_count=0,
    )
    db_session.add(cred)
    db_session.commit()
    db_session.refresh(cred)
    return cred


# ============================================================================
# Service Fixtures
# ============================================================================

@pytest.fixture
def team_service(db_factory):
    """Create a TeamService instance."""
    from file_manager.services.team_service import TeamService
    return TeamService(db_factory=db_factory)


@pytest.fixture
def space_service(db_factory):
    """Create a SpaceService instance."""
    from file_manager.services.space_service import SpaceService
    return SpaceService(db_factory=db_factory)


# ============================================================================
# API Client Fixture
# ============================================================================

@pytest.fixture
def api_client(db_engine, tmp_hermes_home):
    """
    Create a REST API test client.
    Uses the same database engine as db_session for consistency.
    """
    from fastapi.testclient import TestClient
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Import the app
    from file_manager.server import app

    # Override the database dependency to use our test engine
    # This ensures the API uses the same database as our fixtures
    def get_test_db():
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=db_engine)
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    # Override the dependency in the app
    from fastapi import Depends
    from file_manager.services.database import get_db

    app.dependency_overrides[get_db] = get_test_db

    client = TestClient(app)
    yield client

    # Clean up
    app.dependency_overrides.clear()


# ============================================================================
# Lifecycle Context Fixtures
# ============================================================================

@pytest.fixture
def lifecycle_context(db_session, test_user, space, storage_pool):
    """Create a basic lifecycle context."""
    from file_manager.services.lifecycle_engine import LifecycleContext

    return LifecycleContext(
        db_session=db_session,
        user_id=test_user.id,
        space_id=space.id,
        pool_id=storage_pool.id,
    )


# ============================================================================
# Helper Fixtures
# ============================================================================

@pytest.fixture
def pool_with_teams(db_session, test_user, storage_pool):
    """Create a pool with two teams."""
    from file_manager.engine.models import Team

    team1 = Team(
        name="Team A",
        owner_id=test_user.id,
        storage_pool_id=storage_pool.id,
        max_bytes=10 * 1024**3,
        used_bytes=0,
        status="active",
    )
    team2 = Team(
        name="Team B",
        owner_id=test_user.id,
        storage_pool_id=storage_pool.id,
        max_bytes=10 * 1024**3,
        used_bytes=0,
        status="active",
    )
    db_session.add(team1)
    db_session.add(team2)
    db_session.commit()
    db_session.refresh(team1)
    db_session.refresh(team2)

    return {"pool": storage_pool, "team1": team1, "team2": team2}


@pytest.fixture
def space_with_members(db_session, test_user, test_user_2, storage_pool):
    """Create a space with two members."""
    from file_manager.engine.models import Space, SpaceMember

    space = Space(
        name="Team Space",
        storage_pool_id=storage_pool.id,
        owner_id=test_user.id,
        max_bytes=10 * 1024**3,
        used_bytes=0,
        space_type="team",
        status="active",
    )
    db_session.add(space)
    db_session.flush()

    member1 = SpaceMember(
        space_id=space.id,
        user_id=test_user.id,
        role="owner",
        status="active",
    )
    member2 = SpaceMember(
        space_id=space.id,
        user_id=test_user_2.id,
        role="member",
        status="active",
    )
    db_session.add(member1)
    db_session.add(member2)
    db_session.commit()
    db_session.refresh(space)

    return {"space": space, "owner": test_user, "member": test_user_2}
