# Swarm module
from typing import Callable, Any, Optional
from dataclasses import dataclass, field

@dataclass
class Agent:
    """Simple agent class for the swarm."""
    name: str
    instructions: str
    functions: list[Callable] = field(default_factory=list)
    
    def __repr__(self):
        return f"Agent(name={self.name})"

__all__ = ["Agent"]
