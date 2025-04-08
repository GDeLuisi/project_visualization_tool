from src.utility import Singleton,LazyLoader
from typing import Generator
from src._internal import CommitInfo
class CommitLazyLoader(LazyLoader,metaclass=Singleton):
    def __init__(self,generator:Generator[CommitInfo,None,None]=None):
        self.generator=generator
    
    def exist()->bool:
        return Singleton.__exist__(CommitLazyLoader)
    def next(self)->list[CommitInfo]:
        try:
            return next(self.generator)
        except StopIteration:
            CommitLazyLoader.reset()
    def reset():
        Singleton.__delete__(CommitLazyLoader)