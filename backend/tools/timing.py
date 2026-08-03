"""
Tool: timing.

WHEN the career fires - resolves the activator planets against the dasha
timeline into a PAST/ACTIVE/UPCOMING tag and an age window. Wraps TimingResolver.
"""

from core.age_gate import TimingResolver

NAME = "timing"


def run(ctx, activators):
    """Returns {"timing": str, "age_range": str|None, "dasa_context": str|None}"""
    return TimingResolver.resolve(activators, ctx.dashas, ctx.dob, ctx.today)
