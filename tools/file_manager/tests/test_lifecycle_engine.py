"""
Unit tests for LifecycleEngine and LifecycleViolation.
"""

import pytest
from unittest.mock import MagicMock
from file_manager.engine.lifecycle_exception import (
    LifecycleViolation, GuidanceAction, ErrorCode,
    get_lifecycle_engine, set_lifecycle_engine,
)
from file_manager.engine.lifecycle_engine import (
    LifecycleEngine, ConstraintRule, ConstraintType
)


class TestLifecycleViolation:
    """LifecycleViolation exception tests."""

    def test_not_space_member(self):
        """Factory method creates correct violation."""
        error = LifecycleViolation.not_space_member("user-1", "space-1")

        assert error.code == ErrorCode.NOT_SPACE_MEMBER.value
        assert "团队" in error.message
        assert error.guidance.path == "/teams"
        assert error.guidance.label == "加入团队"

    def test_pool_in_use(self):
        """Pool in use violation with team details."""
        teams = [
            {"id": "t1", "name": "Team-A"},
            {"id": "t2", "name": "Team-B"}
        ]
        error = LifecycleViolation.pool_in_use("pool-1", teams)

        assert error.code == ErrorCode.POOL_IN_USE.value
        assert "Team-A" in error.message
        assert "Team-B" in error.message
        assert error.http_status == 409
        assert error.guidance.path == "/admin/teams?pool_id=pool-1"

    def test_quota_exceeded(self):
        """Quota exceeded violation with correct percentage."""
        error = LifecycleViolation.quota_exceeded(
            space_name="项目A",
            used=95 * 1024 * 1024 * 1024,
            max=100 * 1024 * 1024 * 1024,
            required=10 * 1024 * 1024 * 1024
        )

        assert error.code == ErrorCode.SPACE_QUOTA_EXCEEDED.value
        assert "95%" in error.message
        assert error.guidance.path == "/trash"

    def test_not_team_owner(self):
        """Not team owner violation."""
        error = LifecycleViolation.not_team_owner()

        assert error.code == ErrorCode.NOT_TEAM_OWNER.value
        assert error.guidance.action_type == "callback"
        assert error.guidance.callback == "showContactAdminModal"

    def test_no_available_pool(self):
        """No available pool violation."""
        error = LifecycleViolation.no_available_pool()

        assert error.code == ErrorCode.NO_AVAILABLE_POOL.value
        assert error.guidance.action_type == "callback"

    def test_to_dict_format(self):
        """to_dict returns correct format for frontend."""
        error = LifecycleViolation.not_space_member("user-1", "space-1")
        data = error.to_dict()

        # Top-level fields (not wrapped in "error" key)
        assert data["code"] == "NOT_SPACE_MEMBER"
        assert data["message"]
        assert data["details"]["user_id"] == "user-1"
        assert data["details"]["space_id"] == "space-1"
        # guidance is nested
        assert data["guidance"]["label"] == "加入团队"
        assert data["guidance"]["path"] == "/teams"
        assert data["guidance"]["action_type"] == "navigate"


class TestLifecycleEngine:
    """LifecycleEngine constraint tests."""

    @pytest.fixture
    def engine(self):
        """Fresh engine for each test."""
        return LifecycleEngine()

    def test_register_rule(self, engine):
        """Can register a custom rule."""
        rule = ConstraintRule(
            code="TEST_RULE",
            name="测试规则",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("value", 0) > 0,
            error_message="测试失败",
            guidance={"label": "测试", "path": "/test"}
        )
        engine.register_rule(rule)
        assert "TEST_RULE" in engine._rules

    def test_register_action_rule(self, engine):
        """Can associate rule with action."""
        rule = ConstraintRule(
            code="TEST_RULE",
            name="测试规则",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: ctx.get("value", 0) > 0,
            error_message="测试失败",
            guidance={"label": "测试"}
        )
        engine.register_rule(rule)
        engine.register_action_rule("test_action", "TEST_RULE")

        assert "test_action" in engine._action_rules
        assert rule in engine._action_rules["test_action"]

    def test_check_pass(self, engine):
        """Check returns None when constraint passes."""
        context = {"is_member": True, "sufficient_quota": True}
        result = engine.check("upload_file", context)
        assert result is None

    def test_check_fail_member(self, engine):
        """Check returns rule when member constraint fails."""
        context = {"is_member": False, "sufficient_quota": True}
        result = engine.check("upload_file", context)

        assert result is not None
        assert result.code == "NOT_SPACE_MEMBER"

    def test_check_fail_quota(self, engine):
        """Check returns rule when quota constraint fails."""
        context = {"is_member": True, "sufficient_quota": False}
        result = engine.check("upload_file", context)

        assert result is not None
        assert result.code == "QUOTA_SUFFICIENT"

    def test_raise_if_violated(self, engine):
        """Raises LifecycleViolation when constraint fails."""
        context = {"is_member": False}

        with pytest.raises(LifecycleViolation) as exc:
            engine.raise_if_violated("upload_file", context)

        assert exc.value.code == "NOT_SPACE_MEMBER"
        assert exc.value.guidance.label == "加入团队"

    def test_raise_if_violated_passes(self, engine):
        """No exception when constraint passes."""
        context = {"is_member": True}
        # Should not raise
        engine.raise_if_violated("upload_file", context)

    def test_delete_pool_constraint(self, engine):
        """delete_pool action checks team_count."""
        # No teams - should pass
        context = {"team_count": 0}
        result = engine.check("delete_pool", context)
        assert result is None

        # Has teams - should fail
        context = {"team_count": 3}
        result = engine.check("delete_pool", context)
        assert result is not None
        assert result.code == "STORAGE_POOL_IN_USE"

    def test_create_team_constraint(self, engine):
        """create_team action checks available_pools."""
        # Has pools - should pass
        context = {"available_pools": 2}
        result = engine.check("create_team", context)
        assert result is None

        # No pools - should fail
        context = {"available_pools": 0}
        result = engine.check("create_team", context)
        assert result is not None
        assert result.code == "NO_AVAILABLE_POOL"

    def test_delete_space_constraint(self, engine):
        """delete_space action checks member_count."""
        context = {"member_count": 0}
        result = engine.check("delete_space", context)
        assert result is None

        context = {"member_count": 5}
        result = engine.check("delete_space", context)
        assert result is not None
        assert result.code == "SPACE_NO_MEMBERS"

    def test_invite_member_constraint(self, engine):
        """invite_member action checks is_owner."""
        context = {"is_owner": True}
        result = engine.check("invite_member", context)
        assert result is None

        context = {"is_owner": False}
        result = engine.check("invite_member", context)
        assert result is not None
        assert result.code == "NOT_SPACE_OWNER"

    def test_join_team_constraint(self, engine):
        """join_team action checks credential validity."""
        context = {"is_valid": True}
        result = engine.check("join_team", context)
        assert result is None

        context = {"is_valid": False}
        result = engine.check("join_team", context)
        assert result is not None
        assert result.code == "CREDENTIAL_VALID"

    def test_guidance_action_created_correctly(self, engine):
        """Guidance action has correct action_type based on guidance config."""
        context = {"team_count": 1}
        try:
            engine.raise_if_violated("delete_pool", context)
        except LifecycleViolation as e:
            # Path present -> action_type should be "navigate"
            assert e.guidance.action_type == "navigate"
            assert e.guidance.path == "/admin/teams"

        # Now test with callback (no path)
        engine2 = LifecycleEngine()
        rule = ConstraintRule(
            code="TEST_CALLBACK",
            name="Test",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: False,
            error_message="Error",
            guidance={"label": "Contact", "action": "contact_admin"}
        )
        engine2.register_rule(rule)
        engine2.register_action_rule("test_callback", "TEST_CALLBACK")

        try:
            engine2.raise_if_violated("test_callback", {})
        except LifecycleViolation as e:
            assert e.guidance.action_type == "callback"
            assert e.guidance.callback == "contact_admin"


class TestEdgeCases:
    """Edge case handling tests for lifecycle constraints."""

    @pytest.fixture
    def engine(self):
        """Fresh engine for each test."""
        return LifecycleEngine()

    # ========== delete_pool edge cases ==========

    def test_delete_pool_with_migrating_teams(self, engine):
        """Cannot delete pool with teams in migrating state."""
        # Normal case: no teams - should pass
        context = {"team_count": 0}
        result = engine.check("delete_pool", context)
        assert result is None

        # Edge case: teams migrating - should fail
        context = {"team_count": 0, "team_migrating_count": 3}
        result = engine.check("delete_pool", context)
        assert result is not None
        assert result.code == "POOL_TEAMS_MIGRATING"

    def test_delete_pool_with_teams_normal(self, engine):
        """delete_pool fails when teams are using the pool."""
        context = {"team_count": 2, "team_migrating_count": 0}
        result = engine.check("delete_pool", context)
        assert result is not None
        assert result.code == "STORAGE_POOL_IN_USE"

    # ========== upload_file edge cases ==========

    def test_upload_file_quota_reserved(self, engine):
        """Upload blocked when quota is reserved by concurrent uploads."""
        # Normal case: no reservation
        context = {"is_member": True, "sufficient_quota": True, "quota_reserved": 0}
        result = engine.check("upload_file", context)
        assert result is None

        # Edge case: quota reserved by ongoing uploads
        context = {"is_member": True, "sufficient_quota": True, "quota_reserved": 1024 * 1024 * 100}
        result = engine.check("upload_file", context)
        assert result is not None
        assert result.code == "QUOTA_RESERVED"

    def test_upload_file_quota_reserved_override(self, engine):
        """Quota reservation can be overridden with can_override flag."""
        context = {
            "is_member": True,
            "sufficient_quota": True,
            "quota_reserved": 1024 * 1024 * 100,
            "can_override": True
        }
        result = engine.check("upload_file", context)
        assert result is None

    def test_upload_file_member_and_quota(self, engine):
        """Both member and quota checks work together."""
        # Neither member nor quota
        context = {"is_member": False, "sufficient_quota": False}
        result = engine.check("upload_file", context)
        assert result is not None
        assert result.code == "NOT_SPACE_MEMBER"

    # ========== invite_member edge cases ==========

    def test_invite_member_recently_removed(self, engine):
        """Cannot re-invite a recently removed member."""
        # Normal case: not recently removed
        context = {"is_owner": True, "was_recently_removed": False}
        result = engine.check("invite_member", context)
        assert result is None

        # Edge case: member was recently removed
        context = {"is_owner": True, "was_recently_removed": True}
        result = engine.check("invite_member", context)
        assert result is not None
        assert result.code == "MEMBER_RECENTLY_REMOVED"

    def test_invite_member_not_owner(self, engine):
        """Only owner can invite members."""
        context = {"is_owner": False}
        result = engine.check("invite_member", context)
        assert result is not None
        assert result.code == "NOT_SPACE_OWNER"

    # ========== delete_space edge cases ==========

    def test_delete_space_pending_requests(self, engine):
        """Cannot delete space with pending private space requests."""
        # Normal case: no pending requests
        context = {"member_count": 0, "pending_request_count": 0}
        result = engine.check("delete_space", context)
        assert result is None

        # Edge case: has pending requests
        context = {"member_count": 0, "pending_request_count": 2}
        result = engine.check("delete_space", context)
        assert result is not None
        assert result.code == "SPACE_HAS_PENDING_REQUESTS"

    def test_delete_space_has_members(self, engine):
        """Cannot delete space with active members."""
        context = {"member_count": 5, "pending_request_count": 0}
        result = engine.check("delete_space", context)
        assert result is not None
        assert result.code == "SPACE_NO_MEMBERS"

    # ========== join_team edge cases ==========

    def test_join_team_invalid_credential(self, engine):
        """Cannot join team with invalid/expired credential."""
        context = {"is_valid": False}
        result = engine.check("join_team", context)
        assert result is not None
        assert result.code == "CREDENTIAL_VALID"

    def test_join_team_valid_credential(self, engine):
        """Can join team with valid credential."""
        context = {"is_valid": True}
        result = engine.check("join_team", context)
        assert result is None

    # ========== create_team edge cases ==========

    def test_create_team_no_pools(self, engine):
        """Cannot create team when no storage pools available."""
        context = {"available_pools": 0}
        result = engine.check("create_team", context)
        assert result is not None
        assert result.code == "NO_AVAILABLE_POOL"

    def test_create_team_has_pools(self, engine):
        """Can create team when storage pools are available."""
        context = {"available_pools": 3}
        result = engine.check("create_team", context)
        assert result is None

    # ========== Helper method tests ==========

    def test_get_rule_by_code(self, engine):
        """Can retrieve registered rule by code."""
        rule = engine._rules.get("STORAGE_POOL_IN_USE")
        assert rule is not None
        assert rule.code == "STORAGE_POOL_IN_USE"

    def test_get_rules_for_action(self, engine):
        """Can retrieve all rules associated with an action."""
        rules = engine._action_rules.get("upload_file", [])
        # Should have NOT_SPACE_MEMBER and QUOTA_SUFFICIENT (and QUOTA_RESERVED edge case)
        assert len(rules) >= 2
        codes = [r.code for r in rules]
        assert "NOT_SPACE_MEMBER" in codes
        assert "QUOTA_SUFFICIENT" in codes


class TestDatabaseQueryMethods:
    """Tests for LifecycleEngine database query helper methods."""

    @pytest.fixture
    def engine(self):
        """Fresh engine for each test."""
        return LifecycleEngine()

    @pytest.fixture
    def mock_session(self):
        """Create a mock database session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_db_factory(self, mock_session):
        """Create a mock db_factory that returns the session."""
        factory = MagicMock(return_value=mock_session)
        return factory

    # ========== check_membership tests ==========

    def test_check_membership_returns_true_when_member_exists(self, engine, mock_db_factory, mock_session):
        """check_membership returns True when active member is found."""
        mock_member = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_member

        result = engine.check_membership("user-1", "space-1", mock_db_factory)

        assert result is True
        mock_session.query.assert_called_once()

    def test_check_membership_returns_false_when_no_member(self, engine, mock_db_factory, mock_session):
        """check_membership returns False when no active member found."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = engine.check_membership("user-1", "space-1", mock_db_factory)

        assert result is False

    def test_check_membership_closes_session(self, engine, mock_db_factory, mock_session):
        """check_membership properly closes session even on exception."""
        mock_session.query.side_effect = Exception("DB error")

        with pytest.raises(Exception):
            engine.check_membership("user-1", "space-1", mock_db_factory)

        mock_session.close.assert_called_once()

    # ========== check_owner tests ==========

    def test_check_owner_returns_true_when_user_is_owner(self, engine, mock_db_factory, mock_session):
        """check_owner returns True when user owns the space."""
        from unittest.mock import MagicMock
        mock_space = MagicMock()
        mock_space.owner_id = "user-1"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_space

        result = engine.check_owner("user-1", "space-1", mock_db_factory)

        assert result is True

    def test_check_owner_returns_false_when_not_owner(self, engine, mock_db_factory, mock_session):
        """check_owner returns False when user does not own the space."""
        from unittest.mock import MagicMock
        mock_space = MagicMock()
        mock_space.owner_id = "other-user"
        mock_session.query.return_value.filter.return_value.first.return_value = mock_space

        result = engine.check_owner("user-1", "space-1", mock_db_factory)

        assert result is False

    def test_check_owner_returns_false_when_space_not_found(self, engine, mock_db_factory, mock_session):
        """check_owner returns False when space does not exist."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = engine.check_owner("user-1", "space-1", mock_db_factory)

        assert result is False

    # ========== get_team_count_for_pool tests ==========

    def test_get_team_count_for_pool_returns_count(self, engine, mock_db_factory, mock_session):
        """get_team_count_for_pool returns correct team count."""
        mock_session.query.return_value.filter.return_value.count.return_value = 5

        result = engine.get_team_count_for_pool("pool-1", mock_db_factory)

        assert result == 5

    def test_get_team_count_for_pool_returns_zero_when_no_teams(self, engine, mock_db_factory, mock_session):
        """get_team_count_for_pool returns 0 when no teams use the pool."""
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = engine.get_team_count_for_pool("pool-1", mock_db_factory)

        assert result == 0

    # ========== get_member_count_for_space tests ==========

    def test_get_member_count_for_space_returns_count(self, engine, mock_db_factory, mock_session):
        """get_member_count_for_space returns correct active member count."""
        mock_session.query.return_value.filter.return_value.count.return_value = 10

        result = engine.get_member_count_for_space("space-1", mock_db_factory)

        assert result == 10

    # ========== get_available_pool_count tests ==========

    def test_get_available_pool_count_returns_count(self, engine, mock_db_factory, mock_session):
        """get_available_pool_count returns correct active pool count."""
        mock_session.query.return_value.filter.return_value.count.return_value = 3

        result = engine.get_available_pool_count(mock_db_factory)

        assert result == 3

    # ========== get_team_migrating_count tests ==========

    def test_get_team_migrating_count_returns_count(self, engine, mock_db_factory, mock_session):
        """get_team_migrating_count returns correct migrating team count."""
        mock_session.query.return_value.filter.return_value.count.return_value = 2

        result = engine.get_team_migrating_count("pool-1", mock_db_factory)

        assert result == 2

    def test_get_team_migrating_count_returns_zero_when_no_migrating(self, engine, mock_db_factory, mock_session):
        """get_team_migrating_count returns 0 when no teams are migrating."""
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = engine.get_team_migrating_count("pool-1", mock_db_factory)

        assert result == 0

    # ========== check_recently_removed_member tests ==========

    def test_check_recently_removed_member_returns_true_when_recently_removed(self, engine, mock_db_factory, mock_session):
        """check_recently_removed_member returns True when member was removed recently."""
        from unittest.mock import MagicMock
        mock_member = MagicMock()
        mock_session.query.return_value.filter.return_value.first.return_value = mock_member

        result = engine.check_recently_removed_member("user-1", "space-1", mock_db_factory, hours=24)

        assert result is True

    def test_check_recently_removed_member_returns_false_when_not_recent(self, engine, mock_db_factory, mock_session):
        """check_recently_removed_member returns False when member was removed long ago."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        result = engine.check_recently_removed_member("user-1", "space-1", mock_db_factory, hours=24)

        assert result is False

    def test_check_recently_removed_member_custom_hours(self, engine, mock_db_factory, mock_session):
        """check_recently_removed_member respects custom hours parameter."""
        mock_session.query.return_value.filter.return_value.first.return_value = None

        engine.check_recently_removed_member("user-1", "space-1", mock_db_factory, hours=48)

        # Verify the query used the correct hours in filter
        mock_session.query.assert_called_once()

    # ========== get_pending_request_count tests ==========

    def test_get_pending_request_count_returns_count(self, engine, mock_db_factory, mock_session):
        """get_pending_request_count returns correct pending request count."""
        mock_session.query.return_value.filter.return_value.count.return_value = 4

        result = engine.get_pending_request_count("space-1", mock_db_factory)

        assert result == 4

    def test_get_pending_request_count_returns_zero_when_no_pending(self, engine, mock_db_factory, mock_session):
        """get_pending_request_count returns 0 when no pending requests."""
        mock_session.query.return_value.filter.return_value.count.return_value = 0

        result = engine.get_pending_request_count("space-1", mock_db_factory)

        assert result == 0

    # ========== get_quota_reserved tests ==========

    def test_get_quota_reserved_calculates_total(self, engine, mock_db_factory, mock_session):
        """get_quota_reserved calculates total bytes from all uploading files."""
        mock_session.query.return_value.filter.return_value.all.return_value = [
            (1024 * 1024 * 100,),  # 100MB
            (1024 * 1024 * 50,),   # 50MB
        ]

        result = engine.get_quota_reserved("space-1", mock_db_factory)

        assert result == 1024 * 1024 * 150  # 150MB

    def test_get_quota_reserved_returns_zero_when_no_uploads(self, engine, mock_db_factory, mock_session):
        """get_quota_reserved returns 0 when no uploading files."""
        mock_session.query.return_value.filter.return_value.all.return_value = []

        result = engine.get_quota_reserved("space-1", mock_db_factory)

        assert result == 0

    def test_get_quota_reserved_returns_zero_when_none_result(self, engine, mock_db_factory, mock_session):
        """get_quota_reserved returns 0 when query returns None."""
        mock_session.query.return_value.filter.return_value.all.return_value = None

        result = engine.get_quota_reserved("space-1", mock_db_factory)

        assert result == 0


class TestRaiseIfViolatedEdgeCaseLogging:
    """Tests for edge case logging in raise_if_violated."""

    @pytest.fixture
    def engine(self):
        """Fresh engine for each test."""
        return LifecycleEngine()

    def test_raise_if_violated_logs_edge_case_for_pool_teams_migrating(self, engine, caplog):
        """raise_if_violated logs warning for POOL_TEAMS_MIGRATING edge case."""
        import logging
        caplog.set_level(logging.WARNING)

        context = {"team_count": 0, "team_migrating_count": 2}
        try:
            engine.raise_if_violated("delete_pool", context)
        except LifecycleViolation:
            pass

        assert any("Edge case lifecycle violation" in record.message for record in caplog.records)
        assert any("POOL_TEAMS_MIGRATING" in record.message for record in caplog.records)

    def test_raise_if_violated_logs_edge_case_for_quota_reserved(self, engine, caplog):
        """raise_if_violated logs warning for QUOTA_RESERVED edge case."""
        import logging
        caplog.set_level(logging.WARNING)

        context = {
            "is_member": True,
            "sufficient_quota": True,
            "quota_reserved": 1024 * 1024 * 100
        }
        try:
            engine.raise_if_violated("upload_file", context)
        except LifecycleViolation:
            pass

        assert any("Edge case lifecycle violation" in record.message for record in caplog.records)
        assert any("QUOTA_RESERVED" in record.message for record in caplog.records)

    def test_raise_if_violated_logs_edge_case_for_space_pending_requests(self, engine, caplog):
        """raise_if_violated logs warning for SPACE_HAS_PENDING_REQUESTS edge case."""
        import logging
        caplog.set_level(logging.WARNING)

        context = {"member_count": 0, "pending_request_count": 2}
        try:
            engine.raise_if_violated("delete_space", context)
        except LifecycleViolation:
            pass

        assert any("Edge case lifecycle violation" in record.message for record in caplog.records)
        assert any("SPACE_HAS_PENDING_REQUESTS" in record.message for record in caplog.records)

    def test_raise_if_violated_logs_edge_case_for_member_recently_removed(self, engine, caplog):
        """raise_if_violated logs warning for MEMBER_RECENTLY_REMOVED edge case."""
        import logging
        caplog.set_level(logging.WARNING)

        context = {"is_owner": True, "was_recently_removed": True}
        try:
            engine.raise_if_violated("invite_member", context)
        except LifecycleViolation:
            pass

        assert any("Edge case lifecycle violation" in record.message for record in caplog.records)
        assert any("MEMBER_RECENTLY_REMOVED" in record.message for record in caplog.records)

    def test_raise_if_violated_does_not_log_non_edge_case(self, engine, caplog):
        """raise_if_violated does not log warning for non-edge-case violations."""
        import logging
        caplog.set_level(logging.WARNING)

        context = {"is_member": False}
        try:
            engine.raise_if_violated("upload_file", context)
        except LifecycleViolation:
            pass

        # NOT_SPACE_MEMBER is not in the edge_case_codes set
        assert not any("Edge case lifecycle violation" in record.message for record in caplog.records)


class TestCheckMethodExceptionHandling:
    """Tests for exception handling in the check method."""

    @pytest.fixture
    def engine(self):
        """Fresh engine for each test."""
        return LifecycleEngine()

    def test_check_handles_exception_in_check_fn(self, engine):
        """check method catches exceptions from check_fn and continues."""
        # Register a rule with a check_fn that raises an exception
        rule = ConstraintRule(
            code="EXCEPTION_RULE",
            name="Exception Rule",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: (_ for _ in ()).throw(Exception("Test exception")),
            error_message="This should not be seen",
            guidance={"label": "Test"}
        )
        engine.register_rule(rule)
        engine.register_action_rule("test_action", "EXCEPTION_RULE")

        # Register a second rule that should pass
        rule2 = ConstraintRule(
            code="PASSING_RULE",
            name="Passing Rule",
            constraint_type=ConstraintType.PRE_CHECK,
            check_fn=lambda ctx: True,
            error_message="Error",
            guidance={"label": "Test"}
        )
        engine.register_rule(rule2)
        engine.register_action_rule("test_action", "PASSING_RULE")

        # The check should not raise, it should catch the exception and continue
        context = {}
        result = engine.check("test_action", context)

        # Should return None because passing rule passed
        assert result is None
