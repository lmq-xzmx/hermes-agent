"""
Hermes Knowledge Wiki Tools - Integration with llm_wiki

Provides knowledge management capabilities through the hermes-agent tool system.
Interacts with llm_wiki project files directly.

LLM Wiki Architecture:
  - wiki/           → Generated wiki pages (entities, concepts, sources, etc.)
  - raw/sources/    → Original source documents
  - schema.md       → Wiki structure and conventions
  - purpose.md      → Project goals and scope
  - index.md        → Content directory
  - log.md          → Operation history
"""

import json
import os
import re
import hashlib
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

# Add parent directory to path for imports
_tools_dir = Path(__file__).parent.parent
if str(_tools_dir) not in __import__('sys').path:
    __import__('sys').path.insert(0, str(_tools_dir))


# ============================================================================
# Configuration
# ============================================================================

DEFAULT_WIKI_ROOT = os.environ.get(
    "HERMES_WIKI_ROOT",
    str(Path.home() / "hermes-wiki")
)


# ============================================================================
# Tool Schemas
# ============================================================================

KNOWLEDGE_CREATE_PROJECT_SCHEMA = {
    "name": "knowledge_create_project",
    "description": "Create a new knowledge wiki project. Initializes the directory structure, schema.md, purpose.md, and index.md.",
    "parameters": {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Project name (will be used as directory name)"
            },
            "path": {
                "type": "string",
                "description": "Parent directory path where to create the project",
                "default": DEFAULT_WIKI_ROOT
            },
            "purpose": {
                "type": "string",
                "description": "Brief description of the project's purpose",
                "default": ""
            }
        }
    }
}

KNOWLEDGE_OPEN_PROJECT_SCHEMA = {
    "name": "knowledge_open_project",
    "description": "Open/validate an existing knowledge wiki project.",
    "parameters": {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            }
        }
    }
}

KNOWLEDGE_LIST_PROJECTS_SCHEMA = {
    "name": "knowledge_list_projects",
    "description": "List all knowledge wiki projects in the wiki root directory.",
    "parameters": {
        "type": "object",
        "properties": {
            "root": {
                "type": "string",
                "description": "Root directory to search for projects",
                "default": DEFAULT_WIKI_ROOT
            }
        }
    }
}

KNOWLEDGE_READ_PAGE_SCHEMA = {
    "name": "knowledge_read_page",
    "description": "Read a wiki page from the knowledge base.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            },
            "page_path": {
                "type": "string",
                "description": "Relative path to the page within the wiki (e.g., 'entities/gpt-4.md' or 'concepts/rag.md')"
            }
        }
    }
}

KNOWLEDGE_WRITE_PAGE_SCHEMA = {
    "name": "knowledge_write_page",
    "description": "Write a wiki page to the knowledge base. Supports YAML frontmatter.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            },
            "page_path": {
                "type": "string",
                "description": "Relative path within wiki/ (e.g., 'entities/my-entity.md')"
            },
            "content": {
                "type": "string",
                "description": "Page content (with optional YAML frontmatter)"
            },
            "page_type": {
                "type": "string",
                "description": "Page type for frontmatter: entity, concept, source, query, comparison, synthesis",
                "default": "concept"
            },
            "title": {
                "type": "string",
                "description": "Page title"
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Tags for the page",
                "default": []
            },
            "related": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Related page slugs (for cross-referencing)",
                "default": []
            }
        }
    }
}

KNOWLEDGE_SEARCH_SCHEMA = {
    "name": "knowledge_search",
    "description": "Search wiki pages by content using keyword matching. Returns relevant pages with snippets.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            },
            "query": {
                "type": "string",
                "description": "Search query (keywords)"
            },
            "page_type": {
                "type": "string",
                "description": "Filter by page type: entity, concept, source, query, comparison, synthesis",
                "default": ""
            },
            "limit": {
                "type": "integer",
                "description": "Maximum results to return",
                "default": 10
            }
        }
    }
}

KNOWLEDGE_INGEST_SCHEMA = {
    "name": "knowledge_ingest",
    "description": "Ingest a source document into the knowledge wiki. Extracts content and creates wiki pages.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            },
            "source_path": {
                "type": "string",
                "description": "Path to the source document to ingest"
            },
            "source_type": {
                "type": "string",
                "description": "Document type: auto, markdown, pdf, docx, txt",
                "default": "auto"
            }
        }
    }
}

KNOWLEDGE_INDEX_SCHEMA = {
    "name": "knowledge_index",
    "description": "Get the wiki index (table of contents) showing all pages grouped by type.",
    "parameters": {
        "type": "object",
        "properties": {
            "project_path": {
                "type": "string",
                "description": "Path to the wiki project directory"
            }
        }
    }
}


# ============================================================================
# Helper Functions
# ============================================================================

def get_project_root(project_path: str) -> Path:
    """Get the wiki/ subdirectory of a project."""
    root = Path(project_path).expanduser().resolve()
    if not (root / "schema.md").exists():
        raise ValueError(f"Not a valid wiki project: {root}")
    return root


def read_yaml_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML frontmatter from markdown content."""
    import yaml
    match = re.match(r'^---\n(.*?)\n---\n(.*)$', content, re.DOTALL)
    if match:
        try:
            metadata = yaml.safe_load(match.group(1)) or {}
            body = match.group(2)
            return metadata, body
        except yaml.YAMLError:
            pass
    return {}, content


def write_yaml_frontmatter(
    content: str,
    page_type: str = "concept",
    title: str = "",
    tags: List[str] = None,
    related: List[str] = None
) -> str:
    """Add or update YAML frontmatter to content."""
    import yaml

    tags = tags or []
    related = related or []

    metadata = {
        "type": page_type,
        "title": title or Path(content.split('\n')[0]).stem.replace('-', ' ').title(),
        "tags": tags,
        "related": related,
        "updated": datetime.now().strftime("%Y-%m-%d")
    }

    fm = yaml.dump(metadata, default_flow_style=False, allow_unicode=True)
    return f"---\n{fm}---\n{content}"


def validate_page_path(page_path: str) -> bool:
    """Validate that a page path is safe (within wiki/ directory)."""
    normalized = page_path.replace('\\', '/')
    if not normalized.startswith('wiki/'):
        return False
    if '..' in normalized:
        return False
    if normalized.startswith('/') or normalized.startswith('\\'):
        return False
    return True


# ============================================================================
# Tool Implementations
# ============================================================================

def knowledge_create_project(name: str, path: str = DEFAULT_WIKI_ROOT, purpose: str = "", **kwargs) -> dict:
    """Create a new knowledge wiki project."""
    root = Path(path) / name
    if root.exists():
        return {"error": f"Project already exists: {root}"}

    # Create directories
    dirs = [
        "raw/sources",
        "raw/assets",
        "wiki/entities",
        "wiki/concepts",
        "wiki/sources",
        "wiki/queries",
        "wiki/comparisons",
        "wiki/synthesis",
    ]
    for d in dirs:
        (root / d).mkdir(parents=True, exist_ok=True)

    # schema.md
    schema = """# Wiki Schema

## Page Types

| Type | Directory | Purpose |
|------|-----------|---------|
| entity | wiki/entities/ | Named things (models, companies, people, datasets) |
| concept | wiki/concepts/ | Ideas, techniques, phenomena |
| source | wiki/sources/ | Papers, articles, talks, blog posts |
| query | wiki/queries/ | Open questions under investigation |
| comparison | wiki/comparisons/ | Side-by-side analysis of related entities |
| synthesis | wiki/synthesis/ | Cross-cutting summaries and conclusions |

## Naming Conventions

- Files: `kebab-case.md`
- Use `[[page-slug]]` syntax to link between wiki pages

## Frontmatter

All pages must include YAML frontmatter with type, title, tags, related fields.
"""
    (root / "schema.md").write_text(schema)

    # purpose.md
    purpose_content = f"""# Project Purpose

## Goal

{purpose or "<!-- What are you trying to understand or build? -->"}

## Key Questions

<!-- List the primary questions driving this research -->

1.
2.
3.

## Scope

**In scope:**
-

**Out of scope:**
-
"""
    (root / "purpose.md").write_text(purpose_content)

    # wiki/index.md
    index = """# Wiki Index

## Entities

## Concepts

## Sources

## Queries

## Comparisons

## Synthesis
"""
    (root / "wiki/index.md").write_text(index)

    # wiki/log.md
    today = datetime.now().strftime("%Y-%m-%d")
    log = f"""# Research Log

## {today}

- Project created
"""
    (root / "wiki/log.md").write_text(log)

    return {
        "success": True,
        "project": {"name": name, "path": str(root)},
        "message": f"Wiki project created at {root}"
    }


def knowledge_open_project(path: str, **kwargs) -> dict:
    """Open/validate an existing wiki project."""
    root = Path(path).expanduser().resolve()

    if not root.exists():
        return {"error": f"Path does not exist: {root}"}

    if not root.is_dir():
        return {"error": f"Path is not a directory: {root}"}

    if not (root / "schema.md").exists():
        return {"error": f"Not a valid wiki project (missing schema.md): {root}"}

    if not (root / "wiki").is_dir():
        return {"error": f"Not a valid wiki project (missing wiki/ directory): {root}"}

    name = root.name

    # Count pages by type
    page_counts = {}
    for page_type in ["entities", "concepts", "sources", "queries", "comparisons", "synthesis"]:
        count = len(list((root / "wiki" / page_type).glob("*.md")))
        page_counts[page_type] = count

    return {
        "success": True,
        "project": {"name": name, "path": str(root)},
        "page_counts": page_counts
    }


def knowledge_list_projects(root: str = DEFAULT_WIKI_ROOT, **kwargs) -> dict:
    """List all wiki projects in a directory."""
    root_path = Path(root).expanduser().resolve()

    if not root_path.exists():
        return {"success": True, "projects": [], "message": f"Root directory does not exist: {root_path}"}

    projects = []
    for item in root_path.iterdir():
        if item.is_dir() and (item / "schema.md").exists():
            projects.append({
                "name": item.name,
                "path": str(item),
                "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
            })

    return {"success": True, "projects": projects}


def knowledge_read_page(project_path: str, page_path: str, **kwargs) -> dict:
    """Read a wiki page."""
    if not validate_page_path(page_path):
        return {"error": f"Invalid page path (must be within wiki/): {page_path}"}

    root = get_project_root(project_path)
    full_path = root / page_path

    if not full_path.exists():
        return {"error": f"Page not found: {page_path}"}

    content = full_path.read_text()
    metadata, body = read_yaml_frontmatter(content)

    return {
        "success": True,
        "page": {
            "path": page_path,
            "metadata": metadata,
            "content": body,
            "raw": content
        }
    }


def knowledge_write_page(
    project_path: str,
    page_path: str,
    content: str,
    page_type: str = "concept",
    title: str = "",
    tags: List[str] = None,
    related: List[str] = None,
    **kwargs
) -> dict:
    """Write a wiki page."""
    if not validate_page_path(page_path):
        return {"error": f"Invalid page path (must be within wiki/): {page_path}"}

    root = get_project_root(project_path)
    full_path = root / page_path

    # Ensure parent directory exists
    full_path.parent.mkdir(parents=True, exist_ok=True)

    # Add frontmatter if not present
    if not content.strip().startswith('---'):
        content = write_yaml_frontmatter(content, page_type, title, tags, related)

    full_path.write_text(content)

    return {
        "success": True,
        "page": {"path": page_path},
        "message": f"Page written to {page_path}"
    }


def knowledge_search(
    project_path: str,
    query: str,
    page_type: str = "",
    limit: int = 10,
    **kwargs
) -> dict:
    """Search wiki pages by keyword."""
    root = get_project_root(project_path)
    wiki_dir = root / "wiki"

    if not wiki_dir.exists():
        return {"error": f"WIKI directory not found: {wiki_dir}"}

    query_lower = query.lower()
    results = []

    # Search in each type directory
    type_dirs = ["entities", "concepts", "sources", "queries", "comparisons", "synthesis"]
    if page_type:
        type_dirs = [page_type]

    for dtype in type_dirs:
        type_dir = wiki_dir / dtype
        if not type_dir.exists():
            continue

        for md_file in type_dir.glob("*.md"):
            content = md_file.read_text().lower()
            if query_lower in content:
                metadata, body = read_yaml_frontmatter(md_file.read_text())

                # Find snippet around match
                pos = content.find(query_lower)
                start = max(0, pos - 100)
                end = min(len(body), pos + len(query) + 100)
                snippet = body[start:end].strip()

                results.append({
                    "path": str(md_file.relative_to(root)),
                    "type": dtype,
                    "title": metadata.get("title", md_file.stem),
                    "snippet": snippet,
                    "tags": metadata.get("tags", [])
                })

            if len(results) >= limit:
                break

    # Sort by title match first, then content match
    results.sort(key=lambda r: (
        0 if query_lower in r["title"].lower() else 1,
        -r["snippet"].lower().count(query_lower)
    ))

    return {
        "success": True,
        "query": query,
        "count": len(results),
        "results": results[:limit]
    }


def knowledge_ingest(project_path: str, source_path: str, source_type: str = "auto", **kwargs) -> dict:
    """Ingest a source document into the wiki."""
    import subprocess

    root = get_project_root(project_path)
    source = Path(source_path).expanduser().resolve()

    if not source.exists():
        return {"error": f"Source file not found: {source}"}

    # Determine source type
    ext = source.suffix.lower()
    if source_type == "auto":
        if ext == ".pdf":
            source_type = "pdf"
        elif ext in [".docx", ".doc"]:
            source_type = "docx"
        else:
            source_type = "txt"

    # Generate slug from filename
    slug = source.stem.lower().replace(' ', '-').replace('_', '-')

    # Try to extract text content
    content = ""
    if ext == ".md":
        content = source.read_text()
    elif ext == ".txt":
        content = source.read_text()
    elif ext == ".pdf":
        # Try using pdftotext if available
        try:
            result = subprocess.run(
                ["pdftotext", str(source), "-"],
                capture_output=True, text=True, timeout=30
            )
            if result.returncode == 0:
                content = result.stdout
        except (FileNotFoundError, subprocess.TimeoutExpired):
            content = f"[PDF content not extracted - {source.name}]"

    # Create source page
    source_content = f"""# {source.stem.replace('-', ' ').title()}

Source: {source.name}

## Summary

<!-- Brief summary of the document -->

## Key Points

<!-- Main takeaways -->

## Notes

{content[:2000]}{"..." if len(content) > 2000 else ""}
"""

    # Write to sources
    sources_dir = root / "wiki/sources"
    sources_dir.mkdir(parents=True, exist_ok=True)

    source_page_path = sources_dir / f"{slug}.md"
    source_page_path.write_text(write_yaml_frontmatter(
        source_content,
        page_type="source",
        title=source.stem.replace('-', ' ').title(),
        tags=["ingested"],
        related=[]
    ))

    # Copy original to raw/sources
    raw_sources = root / "raw/sources"
    raw_sources.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, raw_sources / source.name)

    return {
        "success": True,
        "source_page": str(source_page_path.relative_to(root)),
        "raw_copy": str(raw_sources / source.name),
        "message": f"Ingested {source.name} into wiki"
    }


def knowledge_index(project_path: str, **kwargs) -> dict:
    """Get wiki index."""
    root = get_project_root(project_path)
    index_path = root / "wiki/index.md"

    if not index_path.exists():
        return {"error": "Index file not found"}

    content = index_path.read_text()

    # Parse index sections
    sections = {}
    current_section = None
    current_items = []

    for line in content.split('\n'):
        if line.startswith('## '):
            if current_section:
                sections[current_section] = current_items
            current_section = line[3:].strip()
            current_items = []
        elif line.startswith('- [[') and current_section:
            current_items.append(line)

    if current_section:
        sections[current_section] = current_items

    return {
        "success": True,
        "project": {"name": root.name, "path": str(root)},
        "index": sections,
        "raw": content
    }


# ============================================================================
# Tool Registration
# ============================================================================

from tools.registry import registry

registry.register(
    name="knowledge_create_project",
    toolset="knowledge",
    schema=KNOWLEDGE_CREATE_PROJECT_SCHEMA,
    handler=lambda args, **kw: knowledge_create_project(
        name=args.get("name"),
        path=args.get("path", DEFAULT_WIKI_ROOT),
        purpose=args.get("purpose", ""),
        **kw
    ),
    emoji="📚",
    description="Create a new knowledge wiki project",
)

registry.register(
    name="knowledge_open_project",
    toolset="knowledge",
    schema=KNOWLEDGE_OPEN_PROJECT_SCHEMA,
    handler=lambda args, **kw: knowledge_open_project(
        path=args.get("path"),
        **kw
    ),
    emoji="📂",
    description="Open/validate an existing wiki project",
)

registry.register(
    name="knowledge_list_projects",
    toolset="knowledge",
    schema=KNOWLEDGE_LIST_PROJECTS_SCHEMA,
    handler=lambda args, **kw: knowledge_list_projects(
        root=args.get("root", DEFAULT_WIKI_ROOT),
        **kw
    ),
    emoji="📋",
    description="List all knowledge wiki projects",
)

registry.register(
    name="knowledge_read_page",
    toolset="knowledge",
    schema=KNOWLEDGE_READ_PAGE_SCHEMA,
    handler=lambda args, **kw: knowledge_read_page(
        project_path=args.get("project_path"),
        page_path=args.get("page_path"),
        **kw
    ),
    emoji="📖",
    description="Read a wiki page",
)

registry.register(
    name="knowledge_write_page",
    toolset="knowledge",
    schema=KNOWLEDGE_WRITE_PAGE_SCHEMA,
    handler=lambda args, **kw: knowledge_write_page(
        project_path=args.get("project_path"),
        page_path=args.get("page_path"),
        content=args.get("content", ""),
        page_type=args.get("page_type", "concept"),
        title=args.get("title", ""),
        tags=args.get("tags", []),
        related=args.get("related", []),
        **kw
    ),
    emoji="✏️",
    description="Write a wiki page",
)

registry.register(
    name="knowledge_search",
    toolset="knowledge",
    schema=KNOWLEDGE_SEARCH_SCHEMA,
    handler=lambda args, **kw: knowledge_search(
        project_path=args.get("project_path"),
        query=args.get("query", ""),
        page_type=args.get("page_type", ""),
        limit=args.get("limit", 10),
        **kw
    ),
    emoji="🔍",
    description="Search wiki pages",
)

registry.register(
    name="knowledge_ingest",
    toolset="knowledge",
    schema=KNOWLEDGE_INGEST_SCHEMA,
    handler=lambda args, **kw: knowledge_ingest(
        project_path=args.get("project_path"),
        source_path=args.get("source_path"),
        source_type=args.get("source_type", "auto"),
        **kw
    ),
    emoji="📥",
    description="Ingest a document into the wiki",
)

registry.register(
    name="knowledge_index",
    toolset="knowledge",
    schema=KNOWLEDGE_INDEX_SCHEMA,
    handler=lambda args, **kw: knowledge_index(
        project_path=args.get("project_path"),
        **kw
    ),
    emoji="📑",
    description="Get wiki index",
)
