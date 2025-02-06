from  dataclasses import dataclass
from typing import Literal
ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]

@dataclass
class SATD():
    satdID: int
    commitID: str
    content: str
    category: ACCEPTED_EXTENSIONS
    file: str
    
@dataclass
class Author():
    email:str
    name:str
    n_files_modified:int
    commits_authored:list[str]
    def __hash__(self):
        return hash(repr(self))
    def __eq__(self, value):
        if not isinstance(value,Author):
            raise TypeError(f"Expected value of type <Author>, received {type(value)}")
        return hash(repr(value))==self.__hash__()
    
@dataclass
class Commit():
    commit_hash:str
    n_modified_lines:int
    modified_filepaths:list[str]
    author:Author

