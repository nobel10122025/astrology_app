"""
Runner - the fixed orchestration path.

1. Auto-discover and load all agents from /agents (never imports by name).
2. Build the immutable ChartContext from user input.
3. Run the applicable agents (all, or filtered by topic).
4. Merge results into a reading.

Agents run in a plain loop: the work is a handful of dict lookups per agent, so
threads would add complexity for no gain (CPU-bound under the GIL).
"""

import importlib
import pkgutil

import agents
from agents.registry import AgentRegistry
from core.chart_context import build_chart_context
from orchestrator.merger import build_reading

_discovered = False
_SKIP_MODULES = {"base_agent", "registry"}


def _discover_agents():
    global _discovered
    if _discovered:
        return
    for _, module_name, _ in pkgutil.iter_modules(agents.__path__):
        if module_name in _SKIP_MODULES:
            continue
        importlib.import_module(f"agents.{module_name}")
    _discovered = True


def run_prediction(data, birth_date=None, topic=None, name=None):
    """Run the full deterministic pipeline. Returns (ctx, results, reading)."""
    _discover_agents()
    ctx = build_chart_context(data, birth_date)
    selected = AgentRegistry.get_for_topic(topic) if topic else AgentRegistry.get_all()
    results = [agent.run(ctx) for agent in selected]
    reading = build_reading(ctx, results, name=name)
    return ctx, results, reading
