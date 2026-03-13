from abc import ABC, abstractmethod
from typing import Any


class BaseServiceResolver(ABC):
    """
    Base class for service resolvers
    """

    @abstractmethod
    def resolve(self, *args, **kwargs) -> Any:
        """
        Resolve a service
        """
        raise NotImplementedError("Subclasses must implement this method")
