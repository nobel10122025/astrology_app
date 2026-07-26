"""
Agent registry.

Concrete agents register an instance at import time. The orchestrator's
auto-discovery imports every module in /agents, which triggers registration -
so adding an agent is: create the file, declare the class, register at the
bottom. Nothing else changes.
"""


class AgentRegistry:
    _agents = {}

    @classmethod
    def register(cls, agent):
        cls._agents[agent.name] = agent

    @classmethod
    def get_all(cls):
        return list(cls._agents.values())

    @classmethod
    def get_for_topic(cls, topic):
        """Return agents whose topics match the query; falls back to all."""
        if not topic:
            return cls.get_all()
        t = topic.lower()
        matches = [
            a for a in cls._agents.values()
            if any(t in kw or kw in t for kw in a.topics)
        ]
        return matches or cls.get_all()
