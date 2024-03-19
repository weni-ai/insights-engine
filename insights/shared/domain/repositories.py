from abc import ABC, abstractclassmethod


class BaseCreateRepository(ABC):
    @abstractclassmethod
    def create(self):
        raise NotImplementedError


class BaseUpdateRepository(ABC):
    @abstractclassmethod
    def update(self):
        raise NotImplementedError


class BaseDeleteRepository(ABC):
    @abstractclassmethod
    def delete(self):
        raise NotImplementedError


class BaseGetRepository(ABC):
    @abstractclassmethod
    def get(self):
        raise NotImplementedError


class BaseListRepository(ABC):
    @abstractclassmethod
    def filter(self):
        raise NotImplementedError
