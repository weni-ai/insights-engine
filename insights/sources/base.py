from abc import ABC, abstractmethod


class BaseQueryExecutor(ABC):
    """
    Base class for query executors
    """

    @classmethod
    @abstractmethod
    def execute(cls, *args, **kwargs):
        raise NotImplementedError("Subclasses must implement this method")
