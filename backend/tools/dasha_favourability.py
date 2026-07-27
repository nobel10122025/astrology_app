"""
Tool: dasha_favourability.

Is the near-future dasha climate favourable? Averages the favourability of the
next N mahadashas. Wraps DasaEvaluator.
"""

from core.dasha_evaluator import DasaEvaluator

NAME = "dasha_favourability"


def run(ctx, count=2):
    """Returns {"favourable": bool, "avg_score": float|None, "periods": [...]}"""
    return DasaEvaluator.outlook(ctx, count=count)
