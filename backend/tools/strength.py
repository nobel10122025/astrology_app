"""
Tool: strength.

HOW GOOD the career is - a 0-10 checklist score over the career houses and their
lords. Wraps ChecklistResolver.
"""

from core.rule_engine import ChecklistResolver

NAME = "strength"


def run(ctx, checklist):
    """Returns {"score": float, "breakdown": [...]}"""
    return ChecklistResolver.resolve(checklist, ctx)
