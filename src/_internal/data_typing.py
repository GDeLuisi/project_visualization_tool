from  dataclasses import dataclass,field
from datetime import date
from time import strptime
from typing import Literal,get_args,Iterable,Optional
import json
import pandas as pd
from pathlib import Path
# ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]
ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]
CONFIG_FOUND=False
config_path=Path(__file__).joinpath("info","ext.json")
if config_path.is_file():
    with config_path.open() as f:
        ACCEPTED_EXTENSIONS:dict[str,str]=json.load(f)
    CONFIG_FOUND=True
    
def check_extension(ext:str,additional_extensions:Iterable[str]=[])->tuple[bool,str]:
    if CONFIG_FOUND:
        if ext not in ACCEPTED_EXTENSIONS:
            return ext in additional_extensions,ext
        return True,ACCEPTED_EXTENSIONS[ext]
    if ext not in get_args(ACCEPTED_EXTENSIONS):
        return ext in additional_extensions,ext
    return True,ext

class DataFrameAdapter():
    def __init__(self):
        pass
    def get_dataframe(self,index:Optional[str]=None)->pd.DataFrame:
        var_dict=self.__dict__.copy()
        for k,v in var_dict.items():
            var_dict[k]=[v]
        df=pd.DataFrame(var_dict)
        if index:
            df.set_index(index,inplace=True,drop=False)
        return df
# {'commit': '1c85669eb58fc986d43eb7c878e03cb58fb4883d', 'abbreviated_commit': '1c85669', 'tree': 'c6a6edfde2001a68e123c724625faf7599f82371', 'abbreviated_tree': 'c6a6edf', 'parent': 'efe6fba7d02ad06bec603b57f2e5115b7ccd31d8', 'abbreviated_parent': 'efe6fba', 'refs': 'HEAD -> development, origin/development', 'encoding': '', 'subject': 'optimized truck factor function', 'sanitized_subject_line': 'optimized-truck-factor-function', 'body': '', 'commit_notes': '', 'verification_flag': 'N', 'signer': '', 'signer_key': '', 'author': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}, 'commiter': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}}
@dataclass
class SATD():
    satdID: int
    commitID: str
    content: str
    category: str
    file: str
    
@dataclass
class Author(DataFrameAdapter):
    email:str
    name:str
    commits_authored:list[str]=field(default_factory=lambda: [])
    def __hash__(self):
        return hash(repr(self.name)+repr(self.email))
    def __eq__(self, value):
        if not isinstance(value,Author):
            raise TypeError(f"Expected value of type <Author>, received {type(value)}")
        return self.name==value.name and self.email==value.email
    def __str__(self):
        return f"Name: {self.name} , Email: {self.email}"
    def toJSON(self):
        return json.dumps(
            self,
            default=lambda o: o.__dict__, 
            sort_keys=True,
            indent=4)
@dataclass
class CommitInfo(DataFrameAdapter):
    commit_hash:str
    abbr_hash:str
    tree:str
    parent:str
    refs:str
    subject:str
    author_name:str
    author_email:str
    date:date
    files:list[str]

