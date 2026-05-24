"""
Lint Service - LLM Wiki 健康检查服务

职责：
- 矛盾检测：同一主题的多个页面表述不一致
- 孤立页面检测：没有被其他页面引用的页面
- 缺失链接检测：引用了不存在页面的 wikilink
- 健康评分：综合评估知识库健康状态
"""

from __future__ import annotations

import re
import logging
from typing import Dict, List, Optional, Tuple, Set, Any
from dataclasses import dataclass
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


# =============================================================================
# Wikilink Parser
# =============================================================================

WIKILINK_PATTERN = re.compile(r'\[\[([^\]|]+)(?:\|[^\]]+)?\]\]')


def extract_wikilinks(content: str) -> List[str]:
    """从 markdown 内容中提取所有 wikilink"""
    return WIKILINK_PATTERN.findall(content)


def extract_title(content: str) -> Optional[str]:
    """从 markdown frontmatter 或 H1 标题提取 title"""
    # Try frontmatter title first
    for line in content.split('\n'):
        line = line.strip()
        if line.startswith('title:'):
            return line.split(':', 1)[1].strip().strip('"')
        if line.startswith('# '):
            return line[2:].strip()

    # Fallback: first heading
    for line in content.split('\n'):
        if line.startswith('# '):
            return line[2:].strip()

    return None


# =============================================================================
# Issue Types
# =============================================================================

class IssueType(str):
    CONTRADICTION = "contradiction"
    ORPHAN_PAGE = "orphan_page"
    BROKEN_LINK = "broken_link"
    DEAD_END_PAGE = "dead_end_page"
    MISSING_SUMMARY = "missing_summary"
    OUTDATED_CONTENT = "outdated_content"


@dataclass
class LintIssue:
    """Lint 问题条目"""
    issue_type: IssueType
    page_path: str
    page_title: Optional[str]
    message: str
    severity: str = "warning"  # error, warning, info
    related_pages: List[str] = None
    evidence: Optional[str] = None


@dataclass
class LintResult:
    """Lint 检查结果"""
    space_id: str
    total_pages: int
    total_issues: int
    issues: List[LintIssue]
    health_score: float  # 0.0 - 1.0
    checked_at: float


# =============================================================================
# Lint Service
# =============================================================================

class LintService:
    """
    LLM Wiki 知识库健康检查服务。

    检测：
    - 矛盾检测：同一概念的不同表述
    - 孤立页面：无入站链接的页面
    - 断裂链接：引用不存在的页面
    - 死末端页面：无出站链接的页面
    - 缺失摘要：没有 LLM 编译摘要的页面
    """

    def __init__(
        self,
        contradiction_threshold: float = 0.7,
        orphan_threshold_days: int = 90,
    ):
        self._contradiction_threshold = contradiction_threshold
        self._orphan_threshold_days = orphan_threshold_days

        # Page graph: page_path -> set of linked page paths
        self._page_graph: Dict[str, Set[str]] = defaultdict(set)
        # Reverse graph: page_path -> set of pages that link to it
        self._reverse_graph: Dict[str, Set[str]] = defaultdict(set)

    def lint_space(
        self,
        space_id: str,
        pages: Dict[str, str],  # path -> content
    ) -> LintResult:
        """
        对整个 Space 进行健康检查。

        Args:
            space_id: Space ID
            pages: {page_path: markdown_content}

        Returns:
            LintResult with all issues
        """
        issues: List[LintIssue] = []

        # Build page graph
        self._build_graph(pages)

        # Run all checks
        issues.extend(self._check_broken_links(pages))
        issues.extend(self._check_orphan_pages(pages))
        issues.extend(self._check_dead_end_pages(pages))
        issues.extend(self._check_missing_summary(pages))
        issues.extend(self._check_contradictions(pages))

        # Calculate health score
        total_checks = len(pages) * 5  # 5 checks per page
        passed_checks = max(0, total_checks - len(issues))
        health_score = passed_checks / total_checks if total_checks > 0 else 1.0

        result = LintResult(
            space_id=space_id,
            total_pages=len(pages),
            total_issues=len(issues),
            issues=issues,
            health_score=health_score,
            checked_at=__import__('time').time(),
        )

        logger.info(
            f"Lint completed for space {space_id}: "
            f"{len(pages)} pages, {len(issues)} issues, "
            f"health score {health_score:.2%}"
        )

        return result

    def _build_graph(self, pages: Dict[str, str]) -> None:
        """Build wikilink graph from pages"""
        self._page_graph.clear()
        self._reverse_graph.clear()

        for page_path, content in pages.items():
            links = extract_wikilinks(content)
            for link in links:
                normalized_link = self._normalize_path(link, page_path)
                self._page_graph[page_path].add(normalized_link)
                self._reverse_graph[normalized_link].add(page_path)

    def _normalize_path(self, link: str, base_path: str) -> str:
        """Normalize wikilink to absolute page path"""
        # Remove anchor
        link = link.split('#')[0]
        # Normalize slashes
        link = link.replace('\\', '/')

        if link.startswith('/'):
            # Absolute path
            return link
        else:
            # Relative path - resolve from base
            base_dir = '/'.join(base_path.split('/')[:-1])
            if base_dir:
                return f"{base_dir}/{link}"
            return link

    def _check_broken_links(
        self,
        pages: Dict[str, str],
    ) -> List[LintIssue]:
        """Check for links to non-existent pages"""
        issues = []

        for page_path, content in pages.items():
            links = extract_wikilinks(content)
            for link in links:
                target = self._normalize_path(link, page_path)

                # Check if target exists
                if target not in pages:
                    issues.append(LintIssue(
                        issue_type=IssueType.BROKEN_LINK,
                        page_path=page_path,
                        page_title=extract_title(content),
                        message=f"Links to non-existent page: [[{link}]]",
                        severity="error",
                        evidence=link,
                    ))

        return issues

    def _check_orphan_pages(
        self,
        pages: Dict[str, str],
    ) -> List[LintIssue]:
        """Check for pages with no inbound links"""
        issues = []

        for page_path, content in pages.items():
            if page_path not in self._reverse_graph or not self._reverse_graph[page_path]:
                issues.append(LintIssue(
                    issue_type=IssueType.ORPHAN_PAGE,
                    page_path=page_path,
                    page_title=extract_title(content),
                    message="Page has no inbound links (orphan page)",
                    severity="warning",
                ))

        return issues

    def _check_dead_end_pages(
        self,
        pages: Dict[str, str],
    ) -> List[LintIssue]:
        """Check for pages with no outbound links"""
        issues = []

        for page_path, content in pages.items():
            if page_path not in self._page_graph or not self._page_graph[page_path]:
                issues.append(LintIssue(
                    issue_type=IssueType.DEAD_END_PAGE,
                    page_path=page_path,
                    page_title=extract_title(content),
                    message="Page has no outbound links (dead end)",
                    severity="info",
                ))

        return issues

    def _check_missing_summary(
        self,
        pages: Dict[str, str],
    ) -> List[LintIssue]:
        """Check for pages without LLM compile summary"""
        issues = []

        for page_path, content in pages.items():
            # Check if page has compiled layer content
            # Typically indicated by frontmatter field or section header
            has_summary = (
                'summary:' in content.lower() or
                '## Summary' in content or
                '## 摘要' in content or
                '> [!summary]' in content
            )

            if not has_summary:
                issues.append(LintIssue(
                    issue_type=IssueType.MISSING_SUMMARY,
                    page_path=page_path,
                    page_title=extract_title(content),
                    message="Page lacks LLM-generated summary",
                    severity="info",
                ))

        return issues

    def _check_contradictions(
        self,
        pages: Dict[str, str],
    ) -> List[LintIssue]:
        """
        Check for potential contradictions between pages.

        This is a simplified check - real contradiction detection
        would require LLM-based semantic analysis.
        """
        issues = []

        # Group pages by title similarity
        title_groups: Dict[str, List[str]] = defaultdict(list)
        for page_path in pages:
            title = extract_title(pages[page_path]) or page_path
            # Simple normalization
            normalized = title.lower().strip()
            title_groups[normalized].append(page_path)

        # Check for duplicate titles
        for title, paths in title_groups.items():
            if len(paths) > 1:
                issues.append(LintIssue(
                    issue_type=IssueType.CONTRADICTION,
                    page_path=paths[0],
                    page_title=title,
                    message=f"Multiple pages with similar title: '{title}'",
                    severity="warning",
                    related_pages=paths[1:],
                ))

        # Check for pages with conflicting timestamps in frontmatter
        # (indicating manual edits after LLM compile)
        for page_path, content in pages.items():
            lines = content.split('\n')
            has_both_clipped_and_edited = False
            for line in lines:
                if 'clipped:' in line.lower():
                    has_both_clipped_and_edited = True
                if has_both_clipped_and_edited and ('last_edited:' in line.lower() or 'modified:' in line.lower()):
                    issues.append(LintIssue(
                        issue_type=IssueType.CONTRADICTION,
                        page_path=page_path,
                        page_title=extract_title(content),
                        message="Page shows signs of manual edit after LLM compile",
                        severity="warning",
                        evidence="Both clipped and modified timestamps present",
                    ))
                    break

        return issues

    # -------------------------------------------------------------------------
    # Utility Methods
    # -------------------------------------------------------------------------

    def get_link_stats(self, page_path: str) -> Dict[str, Any]:
        """Get link statistics for a page"""
        # Outbound links stored directly on the page's graph entry (page_path as-is)
        outbound = len(self._page_graph.get(page_path, set()))
        # Inbound links stored on target path without .md extension
        # (since wikilinks normalize to paths without extension)
        inbound_path = page_path[:-3] if page_path.endswith('.md') else page_path
        inbound = len(self._reverse_graph.get(inbound_path, set()))

        return {
            "page_path": page_path,
            "inbound_links": inbound,
            "outbound_links": outbound,
            "total_links": inbound + outbound,
        }

    def get_most_connected_pages(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get pages with most connections (inbound + outbound)"""
        scores = []
        all_pages = set(self._page_graph.keys()) | set(self._reverse_graph.keys())

        for page in all_pages:
            inbound = len(self._reverse_graph.get(page, set()))
            outbound = len(self._page_graph.get(page, set()))
            scores.append((page, inbound + outbound))

        scores.sort(key=lambda x: x[1], reverse=True)
        return scores[:limit]


# =============================================================================
# Global Lint Service
# =============================================================================

_lint_service: Optional[LintService] = None


def get_lint_service() -> LintService:
    """Get global lint service instance"""
    global _lint_service
    if _lint_service is None:
        _lint_service = LintService()
    return _lint_service