"""
NotebookService - Business logic for Notebook management.

Handles:
- Notebook CRUD operations
- Notebook variables management
- Notebook sharing and duplication
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Dict, Any, Optional

from ..engine.models import Notebook, NotebookVariable, Space, User


# =============================================================================
# Domain Errors
# =============================================================================

class SpaceNotFound(Exception):
    """Space does not exist."""
    pass


class NotebookNotFound(Exception):
    """Notebook does not exist."""
    pass


class NotebookVariableNotFound(Exception):
    """Notebook variable does not exist."""
    pass


class NotNotebookOwner(Exception):
    """Only the notebook owner can perform this action."""
    pass


class NotebookAccessDenied(Exception):
    """Access denied to this notebook."""
    pass


# =============================================================================
# NotebookService
# =============================================================================

class NotebookService:
    """Business logic for Notebook management."""

    def __init__(self, db_factory):
        self._db = db_factory

    def list_notebooks(
        self,
        space_id: Optional[str] = None,
        user_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        include_shared: bool = True,
    ) -> List[Dict[str, Any]]:
        """List notebooks visible to user."""
        session = self._db()
        try:
            query = session.query(Notebook)
            if space_id:
                query = query.filter(Notebook.space_id == space_id)

            if tags:
                for tag in tags:
                    query = query.filter(Notebook.tags.contains(tag))

            notebooks = query.order_by(Notebook.usage_count.desc()).all()

            result = []
            for nb in notebooks:
                if nb.owner_id == user_id:
                    result.append(nb)
                elif nb.is_shared and include_shared:
                    result.append(nb)

            # Omit content in list view for performance
            return [{**n.to_dict(), "content": None} for n in result]
        finally:
            session.close()

    def get_notebook(self, notebook_id: str) -> Dict[str, Any]:
        """Get notebook with full content and variables."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if not nb:
                raise NotebookNotFound()
            return nb.to_dict(include_variables=True)
        finally:
            session.close()

    def create_notebook(
        self,
        space_id: str,
        owner_id: str,
        name: str,
        content: str,
        description: Optional[str] = None,
        is_shared: bool = False,
        tags: Optional[List[str]] = None,
        variables: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """Create a new notebook with optional variables."""
        session = self._db()
        try:
            space = session.query(Space).filter(Space.id == space_id).first()
            if not space:
                raise SpaceNotFound(f"Space {space_id} not found")

            nb = Notebook(
                space_id=space_id,
                owner_id=owner_id,
                name=name,
                description=description,
                content=content,
                is_shared=is_shared,
                tags=tags or [],
            )
            session.add(nb)
            session.flush()

            if variables:
                for var_data in variables:
                    var = NotebookVariable(
                        notebook_id=nb.id,
                        name=var_data["name"],
                        default_value=var_data.get("default_value"),
                        description=var_data.get("description"),
                        is_required=var_data.get("is_required", True),
                    )
                    session.add(var)

            session.commit()
            return nb.to_dict(include_variables=True)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_notebook(
        self,
        notebook_id: str,
        requesting_user_id: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        content: Optional[str] = None,
        is_shared: Optional[bool] = None,
        tags: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Update notebook. Only owner can update."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if not nb:
                raise NotebookNotFound()
            if nb.owner_id != requesting_user_id:
                raise NotNotebookOwner()

            if name is not None:
                nb.name = name
            if description is not None:
                nb.description = description
            if content is not None:
                nb.content = content
            if is_shared is not None:
                nb.is_shared = is_shared
            if tags is not None:
                nb.tags = tags

            nb.updated_at = datetime.utcnow()
            session.commit()
            return nb.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_notebook(self, notebook_id: str, requesting_user_id: str) -> None:
        """Delete notebook. Only owner can delete."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if not nb:
                raise NotebookNotFound()
            if nb.owner_id != requesting_user_id:
                raise NotNotebookOwner()
            session.delete(nb)
            session.commit()
        finally:
            session.close()

    def add_variable(
        self,
        notebook_id: str,
        requesting_user_id: str,
        name: str,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
        is_required: bool = True,
    ) -> Dict[str, Any]:
        """Add a variable to a notebook."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if not nb:
                raise NotebookNotFound()
            if nb.owner_id != requesting_user_id:
                raise NotNotebookOwner()

            var = NotebookVariable(
                notebook_id=notebook_id,
                name=name,
                default_value=default_value,
                description=description,
                is_required=is_required,
            )
            session.add(var)
            session.commit()
            return var.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def update_variable(
        self,
        variable_id: str,
        requesting_user_id: str,
        name: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
        is_required: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Update a notebook variable."""
        session = self._db()
        try:
            var = session.query(NotebookVariable).filter(
                NotebookVariable.id == variable_id
            ).first()
            if not var:
                raise NotebookVariableNotFound()

            nb = var.notebook
            if nb.owner_id != requesting_user_id:
                raise NotNotebookOwner()

            if name is not None:
                var.name = name
            if default_value is not None:
                var.default_value = default_value
            if description is not None:
                var.description = description
            if is_required is not None:
                var.is_required = is_required

            session.commit()
            return var.to_dict()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def delete_variable(self, variable_id: str, requesting_user_id: str) -> None:
        """Delete a notebook variable."""
        session = self._db()
        try:
            var = session.query(NotebookVariable).filter(
                NotebookVariable.id == variable_id
            ).first()
            if not var:
                raise NotebookVariableNotFound()

            nb = var.notebook
            if nb.owner_id != requesting_user_id:
                raise NotNotebookOwner()

            session.delete(var)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def increment_usage(self, notebook_id: str) -> None:
        """Increment usage counter when notebook is accessed."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if nb:
                nb.usage_count += 1
                session.commit()
        finally:
            session.close()

    def duplicate_notebook(
        self,
        notebook_id: str,
        new_owner_id: str,
        new_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a copy of a notebook."""
        session = self._db()
        try:
            nb = session.query(Notebook).filter(Notebook.id == notebook_id).first()
            if not nb:
                raise NotebookNotFound()

            if not nb.is_shared and nb.owner_id != new_owner_id:
                raise NotebookAccessDenied()

            new_nb = Notebook(
                space_id=nb.space_id,
                owner_id=new_owner_id,
                name=new_name or f"{nb.name} (copy)",
                description=nb.description,
                content=nb.content,
                is_shared=False,
                tags=list(nb.tags) if nb.tags else [],
            )
            session.add(new_nb)
            session.flush()

            for var in nb.variables:
                new_var = NotebookVariable(
                    notebook_id=new_nb.id,
                    name=var.name,
                    default_value=var.default_value,
                    description=var.description,
                    is_required=var.is_required,
                )
                session.add(new_var)

            session.commit()
            return new_nb.to_dict(include_variables=True)
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
