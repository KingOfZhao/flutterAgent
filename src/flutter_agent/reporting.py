"""Deterministic PRD markdown decorations.

Two pure functions that wrap the model's markdown with mechanically-derived
sections so the audit trail and dependency warnings are always visible,
independent of what the model chose to write.
"""
from __future__ import annotations

from typing import List, Optional

from .schemas import PackageValidation, ReviewPass


def prepend_validation_warnings(
    markdown: Optional[str], validations: List[PackageValidation]
) -> Optional[str]:
    """Prepend a dependency-validation warning banner when any package failed
    pub.dev verification."""
    if not markdown:
        return markdown
    bad = [
        v
        for v in validations
        if not v.exists or v.constraint_ok is False or v.is_discontinued
    ]
    if not bad:
        return markdown
    lines = [
        "> ⚠️ **依赖校验告警** — 以下包未能在 pub.dev 验证通过,合入代码前请复核:",
    ]
    for v in bad:
        tag = "❌" if not v.exists else ("⚠️" if v.is_discontinued else "❓")
        lines.append(
            f"> - {tag} `{v.package}` (声明 {v.declared_version or '—'}, "
            f"pub.dev latest={v.latest or 'n/a'}) — {v.reason or 'see validations'}"
        )
    return "\n".join(lines) + "\n\n" + markdown


def append_audit_section(
    markdown: Optional[str],
    review_history: List[ReviewPass],
    acceptance_gaps: List[dict],
) -> Optional[str]:
    """Append a deterministic audit block (closed-loop passes + acceptance
    gaps) to the PRD so the mechanical checks are always visible, even if the
    model's markdown omits them."""
    if not markdown or (not review_history and not acceptance_gaps):
        return markdown
    lines = ["", "---", "", "## 闭环与自检审计(自动生成)", ""]
    if review_history:
        lines.append("### 评审闭环")
        lines.append("")
        lines.append("| 轮次 | findings | blocker/major/minor | 来源(llm/static) | blocking |")
        lines.append("| --- | --- | --- | --- | --- |")
        for p in review_history:
            sev = "/".join(str(p.by_severity.get(k, 0)) for k in ("blocker", "major", "minor"))
            src = f"{p.by_source.get('llm', 0)}/{p.by_source.get('static', 0)}"
            lines.append(
                f"| {p.iteration} | {p.findings} | {sev} | {src} | {'是' if p.blocking else '否'} |"
            )
        lines.append("")
    if acceptance_gaps:
        lines.append("### 验收交叉校验缺口")
        lines.append("")
        lines.append("| 对象 | 严重度 | 问题 |")
        lines.append("| --- | --- | --- |")
        for g in acceptance_gaps:
            lines.append(
                f"| {g.get('path', '?')} | {g.get('severity', '?')} | {g.get('issue', '')} |"
            )
        lines.append("")
    return markdown + "\n".join(lines)
