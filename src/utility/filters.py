from typing import Callable,Iterable,Any,Generator

filter_registry:dict[str,Callable[...,bool]]=dict()
sort_registry:dict[str,Callable[...,Iterable]]=dict()
class Filter():
    def __init__(self,fun:Callable[...,bool]):
        self.fun=fun
        
    def run(self,values:Iterable,comparison)->Generator[Any,None,None]:
        for v in values:
            if self.fun(v,comparison):
                yield v
                
class FilterFactory():
    def __init__(self):
        pass
    def create_filter(name:str)->Filter:
        # print(filter_registry)
        if not name in filter_registry:
            return Filter(lambda a: True)
        return Filter(filter_registry[name])
    
def filter(name:str):
    def decorator(fun:Callable[...,bool]):
        filter_registry[name]=fun
        def wrapper():
            fun()
            return
        return wrapper
    return decorator

def sorter_provider(name:str):
    if not name in sort_registry:
        return None
    return sort_registry[name]

def sorter(name:str):
    def decorator(fun:Callable[...,bool]):
        sort_registry[name]=fun
        def wrapper():
            fun()
            return
        return wrapper
    return decorator