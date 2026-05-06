"""
团队配额集成测试

测试以下功能：
1. 配额状态查询
2. 新成员加入配额检查
3. 配额不足时拒绝加入
"""

import pytest
import sys
from pathlib import Path

# Make file_manager importable
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from tools.file_manager.services.team_service import TeamService, TeamNotFound


class TestTeamQuota:
    """团队配额测试"""

    @pytest.fixture
    def team_service(self, db_factory):
        """创建 TeamService 实例"""
        return TeamService(db_factory=db_factory)

    @pytest.fixture
    def sample_team_id(self, team_service, test_user, storage_pool):
        """创建测试团队"""
        team = team_service.create_team(
            name="测试团队",
            owner_id=test_user.id,
            storage_pool_id=storage_pool.id,
            max_bytes=1024 * 1024 * 100  # 100MB
        )
        return team["id"]

    def test_check_quota_for_new_member_success(self, team_service, sample_team_id):
        """测试配额足够时允许新成员加入"""
        can_join, message = team_service.check_team_quota_for_new_member(
            team_id=sample_team_id,
            member_quota=1024 * 1024 * 10  # 10MB
        )
        assert can_join is True
        assert "配额足够" in message

    def test_check_quota_for_new_member_fail(self, team_service, sample_team_id):
        """测试配额不足时拒绝新成员加入"""
        can_join, message = team_service.check_team_quota_for_new_member(
            team_id=sample_team_id,
            member_quota=1024 * 1024 * 200  # 200MB，超过100MB上限
        )
        assert can_join is False
        assert "配额不足" in message

    def test_get_team_quota_status(self, team_service, sample_team_id):
        """测试获取团队配额状态"""
        status = team_service.get_team_quota_status(sample_team_id)
        assert "max_bytes" in status
        assert "used_bytes" in status
        assert "available_bytes" in status
        assert status["max_bytes"] == 1024 * 1024 * 100

    def test_team_not_found(self, team_service):
        """测试团队不存在时抛出异常"""
        with pytest.raises(TeamNotFound):
            team_service.check_team_quota_for_new_member(
                team_id="non-existent-team-id",
                member_quota=1024 * 1024 * 10
            )