from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Abstract base class for all agents in the AI Travel Buddy system.
    Each agent must implement the run() method.
    """

    @abstractmethod
    def run(self, input_data: Any) -> Any:
        """
        Processes input_data and returns the agent's output.
        This method must be implemented by all child agents.
        """
        pass
