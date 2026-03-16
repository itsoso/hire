from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class AgentMessage:
    task_id: str
    agent_type: str
    action: str
    payload: dict = field(default_factory=dict)
    result: dict | None = None
    status: str = "pending"
