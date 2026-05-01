"""
WorkflowService - Business logic for Workflow management.

Handles:
- Workflow CRUD operations
- Workflow steps management
- Workflow sharing and duplication
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from ..engine.models import Workflow, WorkflowStep, Space, User


# =============================================================================
# Domain Errors
# =============================================================================

class WorkflowNotFound(Exception):
    """Workflow does not exist."""
    pass


class WorkflowStepNotFound(Exception):
    """Workflow step does not exist."""
    pass


class NotWorkflowOwner(Exception):
    """Only the workflow owner can perform this action."""
    pass


class WorkflowAccessDenied(Exception):
    """Access denied to this workflow."""
    pass


# =============================================================================
# WorkflowService
# =============================================================================

class WorkflowService:
    """Business logic for Workflow management."""

    def __init__(self, db_factory):
        self._db = db_factory

    def list_workflows(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_shared: bool = True,
    ) -> List[Dict[str, Any]]:
        """List workflows visible to user in a space."""
        session = self._db()
        try:
            query = session.query(Workflow)
            if space_id:
                query = query.filter(Workflow.space_id == space_id)

            if tags:
                for tag in tags:
                    query = query.filter(Workflow.tags.contains(tag))

            workflows = query.order_by(Workflow.usage_count.desc()).all()

            # Filter by access: own + shared (if include_shared)
            result = []
            for w in workflows:
                if w.owner_id == user_id:
                    result.append(w)
                elif w.is_shared and include_shared:
                    result.append(w)
            return [w.to_dict() for w in result]
        finally:
            session.close()

    def get_workflow(self, workflow_id: str) -> Dict[str, Any]:
        """Get workflow with all steps."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound(f"Workflow {workflow_id} not found")
            return wf.to_dict(include_steps=True)
        finally:
            session.close()

    def create_workflow(
        self,
        space_id: str,
        owner_id: str,
        name: str,
        description: Optional[str] = None,
        is_shared: bool = False,
        tags: Optional[List[str]] = None,
        steps: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new workflow with optional steps."""
        session = self._db()
        try:
            # Verify space exists
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"Space {space_id} not found")

            wf = Workflow(
                space_id=space_id,
                owner_id=owner_id,
                name=name,
                description=description,
                is_shared=is_shared,
                tags=tags or [],
            )
            session.add(wf)
            session.flush()

            # Add steps if provided
            if steps:
                for idx, step_data in enumerate(steps, start=1):
                    step = WorkflowStep(
                        workflow_id=wf.id,
                        order=step_data.get("order", idx),
                        command=step_data["command"],
                        explanation=step_data.get("explanation"),
                        confirm_required=step_data.get("confirm_required", False),
                    )
                    session.add(step)

            session.commit()
            return wf.to_dict(include_steps=True)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_workflow(
        self,
        workflow_id: str,
        requesting_user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        is_shared: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update workflow metadata. Only owner can update."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound()
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()

            if name is not None:
                wf.name = name
            if description is not None:
                wf.description = description
            if is_shared is not None:
                wf.is_shared = is_shared
            if tags is not None:
                wf.tags = tags

            wf.updated_at = datetime.utcnow()
            session.commit()
            return wf.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_workflow(self, workflow_id: str, requesting_user_id: str) -> None:
        """Delete a workflow. Only owner can delete."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound()
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()
            session.delete(wf)
            session.commit()
        finally:
            session.close()

    def add_step(
        self,
        workflow_id: str,
        requesting_user_id: str,
        order: int,
        command: str,
        explanation: Optional[str] = None,
        confirm_required: bool = False,
    ) -> Dict[str, Any]:
        """Add a step to a workflow."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound()
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()

            step = WorkflowStep(
                workflow_id=workflow_id,
                order=order,
                command=command,
                explanation=explanation,
                confirm_required=confirm_required,
            )
            session.add(step)

            wf.updated_at = datetime.utcnow()
            session.commit()
            return step.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_step(
        self,
        step_id: str,
        requesting_user_id: str,
        order: Optional[int] = None,
        command: Optional[str] = None,
        explanation: Optional[str] = None,
        confirm_required: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a workflow step."""
        session = self._db()
        try:
            step = session.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
            if not step:
                raise WorkflowStepNotFound()

            wf = step.workflow
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()

            if order is not None:
                step.order = order
            if command is not None:
                step.command = command
            if explanation is not None:
                step.explanation = explanation
            if confirm_required is not None:
                step.confirm_required = confirm_required

            session.commit()
            return step.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_step(self, step_id: str, requesting_user_id: str) -> None:
        """Delete a workflow step."""
        session = self._db()
        try:
            step = session.query(WorkflowStep).filter(WorkflowStep.id == step_id).first()
            if not step:
                raise WorkflowStepNotFound()

            wf = step.workflow
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()

            session.delete(step)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def reorder_steps(
        self,
        workflow_id: str,
        requesting_user_id: str,
        step_ids: List[str],
    ) -> List[Dict[str, Any]]:
        """Reorder workflow steps. step_ids must contain all step IDs in new order."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound()
            if wf.owner_id != requesting_user_id:
                raise NotWorkflowOwner()

            for idx, step_id in enumerate(step_ids, start=1):
                step = session.query(WorkflowStep).filter(
                    WorkflowStep.id == step_id,
                    WorkflowStep.workflow_id == workflow_id,
                ).first()
                if step:
                    step.order = idx

            session.commit()
            steps = session.query(WorkflowStep).filter(
                WorkflowStep.workflow_id == workflow_id
            ).order_by(WorkflowStep.order).all()
            return [s.to_dict() for s in steps]
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_usage(self, workflow_id: str) -> None:
        """Increment usage counter when workflow is executed."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if wf:
                wf.usage_count += 1
                session.commit()
        finally:
            session.close()

    def duplicate_workflow(
        self,
        workflow_id: str,
        new_owner_id: str,
        new_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a copy of a workflow for a user."""
        session = self._db()
        try:
            wf = session.query(Workflow).filter(Workflow.id == workflow_id).first()
            if not wf:
                raise WorkflowNotFound()

            # Only owner or shared workflows can be duplicated
            if not wf.is_shared and wf.owner_id != new_owner_id:
                raise WorkflowAccessDenied()

            new_wf = Workflow(
                space_id=wf.space_id,
                owner_id=new_owner_id,
                name=new_name or f"{wf.name} (copy)",
                description=wf.description,
                is_shared=False,  # Duplicated workflow is private by default
                tags=list(wf.tags) if wf.tags else [],
            )
            session.add(new_wf)
            session.flush()

            # Duplicate all steps
            for step in wf.steps:
                new_step = WorkflowStep(
                    workflow_id=new_wf.id,
                    order=step.order,
                    command=step.command,
                    explanation=step.explanation,
                    confirm_required=step.confirm_required,
                )
                session.add(new_step)

            session.commit()
            return new_wf.to_dict(include_steps=True)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
