from  dataclasses import dataclass

@dataclass
class SATD():
    satdID: int
    commitID: str
    description: str
    category: str
    
@dataclass
class Author():
    email:str
    name:str
    def __hash__(self):
        return hash(repr(self))
    def __eq__(self, value):
        if not isinstance(value,Author):
            raise TypeError(f"Expected value of type <Author>, received {type(value)}")
        return hash(repr(value))==self.__hash__()