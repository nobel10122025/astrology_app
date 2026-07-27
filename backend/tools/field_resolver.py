"""
Tool: field_resolver.

WHAT field - combines the significations (meaning tags) of the career planets
into ranked specific fields (e.g. government + astronomy -> ISRO/NASA). Wraps
signification.resolve_fields.
"""

from core.signification import resolve_fields

NAME = "field_resolver"


def run(ctx, career_planets):
    """Returns the field_profile: tag_bag, sources, influence, influence_parts,
    and the ranked fields."""
    return resolve_fields(career_planets, ctx)
