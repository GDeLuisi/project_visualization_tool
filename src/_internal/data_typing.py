from  dataclasses import dataclass,field
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
    n_files_modified:int=0
    commits_authored:list[str]=field(default_factory=lambda: [])
    def __hash__(self):
        return hash(repr(self))
    def __eq__(self, value):
        if not isinstance(value,Author):
            raise TypeError(f"Expected value of type <Author>, received {type(value)}")
        return self.name==value.name and self.email==value.email
    
@dataclass
class Commit():
    commit_hash:str
    n_modified_lines:int
    modified_filepaths:list[str]
    author:Author

