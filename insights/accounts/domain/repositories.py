from abc import ABC, abstractclassmethod


class UserRepository(ABC):
    @abstractclassmethod
    def get(self):
        raise NotImplementedError

    @abstractclassmethod
    def create(self):
        raise NotImplementedError

    @abstractclassmethod
    def get_or_create(self):
        raise NotImplementedError

    @abstractclassmethod
    def update(self):
        raise NotImplementedError

    @abstractclassmethod
    def delete(self):
        raise NotImplementedError
