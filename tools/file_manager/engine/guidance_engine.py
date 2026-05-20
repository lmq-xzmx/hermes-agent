"""
Guidance Engine - Event-driven user guidance system.

Coordinates with EventBus for event subscription and LifecycleEngine for constraint checking.
"""

from __future__ import annotations
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class GuidanceEvent(str, Enum):
    """Guidance trigger events."""
    # Auth events
    USER_REGISTER = "guidance.user_register"
    USER_LOGIN = "guidance.user_login"

    # Space/Team events
    TEAM_CREATED = "guidance.team_created"
    SPACE_CREATED = "guidance.space_created"
    MEMBER_INVITED = "guidance.member_invited"

    # File operations
    FIRST_FILE_UPLOAD = "guidance.first_file_upload"
    FILE_UPLOAD_COMPLETE = "guidance.file_upload_complete"

    # Tour events
    TOUR_START = "guidance.tour_start"
    TOUR_COMPLETE = "guidance.tour_complete"
    TOUR_STEP = "guidance.tour_step"


@dataclass
class GuidanceStep:
    """Single step in a guidance tour."""
    id: str
    title: str
    content: str
    target_selector: Optional[str] = None
    position: str = "bottom"  # top, bottom, left, right, center
    button_text: str = "下一步"
    button_action: Optional[str] = None


@dataclass
class GuidanceTour:
    """A guided workflow tour."""
    id: str
    name: str
    description: str
    steps: List[GuidanceStep]
    trigger_event: GuidanceEvent
    conditions: Dict[str, Any] = field(default_factory=dict)

    def check_conditions(self, context: Dict[str, Any]) -> bool:
        """Check if all conditions are met."""
        for key, expected in self.conditions.items():
            actual = context.get(key)
            if actual != expected:
                return False
        return True


@dataclass
class GuidanceContext:
    """Context passed when guidance is triggered."""
    user_id: str
    event: GuidanceEvent
    data: Dict[str, Any] = field(default_factory=dict)


class GuidanceEngine:
    """
    Guidance Engine - coordinates user guidance across the application.

    Features:
    - Event-driven trigger via EventBus
    - Constraint-aware (uses LifecycleEngine)
    - Tour management
    - Progress tracking
    """

    def __init__(self, event_bus, lifecycle_engine=None):
        self._event_bus = event_bus
        self._lifecycle_engine = lifecycle_engine
        self._tours: Dict[GuidanceEvent, List[GuidanceTour]] = {}
        self._user_progress: Dict[str, Dict[str, int]] = {}  # user_id -> tour_id -> step
        self._handlers: Dict[GuidanceEvent, List[Callable]] = {}
        self._init_default_tours()
        self._subscribe_to_events()

    def _init_default_tours(self):
        """Initialize default guidance tours."""
        # First team creation tour
        self.register_tour(GuidanceTour(
            id="create_team_tour",
            name="创建团队引导",
            description="学习如何创建第一个团队",
            trigger_event=GuidanceEvent.TEAM_CREATED,
            conditions={"is_first": True},
            steps=[
                GuidanceStep(
                    id="step1",
                    title="团队创建成功",
                    content="恭喜！你已成功创建第一个团队。现在邀请成员加入吧。",
                    position="center",
                    button_text="邀请成员"
                ),
                GuidanceStep(
                    id="step2",
                    title="添加成员",
                    content="点击团队设置中的「邀请成员」按钮，输入邮箱发送邀请。",
                    target_selector=".team-settings .invite-btn",
                    position="right",
                    button_text="我知道了"
                ),
            ]
        ))

        # First file upload tour
        self.register_tour(GuidanceTour(
            id="upload_file_tour",
            name="上传文件引导",
            description="学习如何上传第一个文件",
            trigger_event=GuidanceEvent.FIRST_FILE_UPLOAD,
            conditions={"is_first": True},
            steps=[
                GuidanceStep(
                    id="step1",
                    title="上传成功",
                    content="文件上传成功！你现在可以管理文件了。",
                    position="center",
                    button_text="完成引导"
                ),
            ]
        ))

    def register_tour(self, tour: GuidanceTour):
        """Register a guidance tour."""
        if tour.trigger_event not in self._tours:
            self._tours[tour.trigger_event] = []
        self._tours[tour.trigger_event].append(tour)
        logger.debug(f"Registered tour: {tour.id} for event {tour.trigger_event.value}")

    def register_handler(self, event: GuidanceEvent, handler: Callable):
        """Register a handler for a guidance event."""
        if event not in self._handlers:
            self._handlers[event] = []
        self._handlers[event].append(handler)

    def _subscribe_to_events(self):
        """Subscribe to EventBus events."""
        for event_type in GuidanceEvent:
            self._event_bus.subscribe(
                self._map_event_type(event_type),
                lambda e: self._handle_event(e)
            )

    def _map_event_type(self, guidance_event: GuidanceEvent):
        """Map GuidanceEvent to EventType."""
        from ..services.event_bus import EventType
        mapping = {
            GuidanceEvent.USER_REGISTER: EventType.AUTH_REGISTER,
            GuidanceEvent.USER_LOGIN: EventType.AUTH_LOGIN_SUCCESS,
            GuidanceEvent.TEAM_CREATED: EventType.ADMIN_USER_CREATE,
            GuidanceEvent.FIRST_FILE_UPLOAD: EventType.FILE_WRITE,
        }
        return mapping.get(guidance_event, EventType.GUIDANCE_TRIGGER)

    def _handle_event(self, event):
        """Handle incoming event from EventBus."""
        try:
            guidance_event = self._detect_guidance_event(event)
            if guidance_event:
                context = self._build_context(event)
                self.trigger(guidance_event, context)
        except Exception as e:
            logger.exception(f"Error handling guidance event: {e}")

    def _detect_guidance_event(self, event) -> Optional[GuidanceEvent]:
        """Detect which guidance event this is."""
        event_type_map = {
            "auth.register": GuidanceEvent.USER_REGISTER,
            "auth.login.success": GuidanceEvent.USER_LOGIN,
            "admin.user_create": GuidanceEvent.TEAM_CREATED,
            "file.write": GuidanceEvent.FIRST_FILE_UPLOAD,
        }
        event_value = event.type.value if hasattr(event.type, 'value') else str(event.type)
        return event_type_map.get(event_value)

    def _build_context(self, event) -> GuidanceContext:
        """Build guidance context from event."""
        return GuidanceContext(
            user_id=event.data.get("user_id", ""),
            event=self._detect_guidance_event(event) or GuidanceEvent.USER_LOGIN,
            data=event.data
        )

    def trigger(self, event: GuidanceEvent, context: GuidanceContext):
        """Trigger guidance for a specific event."""
        tours = self._tours.get(event, [])

        for tour in tours:
            if tour.check_conditions(context.data):
                # Check lifecycle constraints before showing guidance
                if self._lifecycle_engine:
                    constraint = self._lifecycle_engine.check("show_guidance", context.data)
                    if constraint:
                        logger.debug(f"Constraint {constraint.code} prevents guidance: {tour.id}")
                        continue

                self._start_tour(tour, context)

    def _start_tour(self, tour: GuidanceTour, context: GuidanceContext):
        """Start a guidance tour for a user."""
        user_id = context.user_id
        if user_id not in self._user_progress:
            self._user_progress[user_id] = {}

        self._user_progress[user_id][tour.id] = 0

        # Notify handlers
        handlers = self._handlers.get(tour.trigger_event, [])
        for handler in handlers:
            try:
                handler(tour, context)
            except Exception as e:
                logger.exception(f"Guidance handler error: {e}")

        logger.info(f"Started tour {tour.id} for user {user_id}")

    def get_tour_progress(self, user_id: str, tour_id: str) -> int:
        """Get current step index for a user's tour."""
        return self._user_progress.get(user_id, {}).get(tour_id, 0)

    def advance_step(self, user_id: str, tour_id: str) -> Optional[GuidanceStep]:
        """Advance to next step in tour."""
        if user_id not in self._user_progress:
            return None

        tours = [t for tours in self._tours.values() for t in tours if t.id == tour_id]
        if not tours:
            return None

        tour = tours[0]
        current_step = self._user_progress[user_id].get(tour_id, 0)

        if current_step >= len(tour.steps) - 1:
            # Tour complete
            del self._user_progress[user_id][tour_id]
            return None

        self._user_progress[user_id][tour_id] = current_step + 1
        return tour.steps[current_step + 1]

    def get_current_step(self, user_id: str, tour_id: str) -> Optional[GuidanceStep]:
        """Get current step for a tour."""
        if user_id not in self._user_progress:
            return None

        tours = [t for tours in self._tours.values() for t in tours if t.id == tour_id]
        if not tours:
            return None

        tour = tours[0]
        step_index = self._user_progress[user_id].get(tour_id, 0)

        if step_index >= len(tour.steps):
            return None

        return tour.steps[step_index]


# Global instance
_guidance_engine: Optional[GuidanceEngine] = None


def get_guidance_engine() -> GuidanceEngine:
    """Get the global GuidanceEngine instance."""
    global _guidance_engine
    if _guidance_engine is None:
        from ..services.event_bus import get_event_bus
        from .lifecycle_engine import get_lifecycle_engine
        _guidance_engine = GuidanceEngine(get_event_bus(), get_lifecycle_engine())
    return _guidance_engine