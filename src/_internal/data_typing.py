from  dataclasses import dataclass,field
from datetime import date
from time import strptime
from .exceptions import ObjectNotInTreeError
from typing import Literal,get_args,Iterable,Optional,Union,Generator
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
    def get_dataframe(self)->pd.DataFrame:
        var_dict=self.__dict__.copy()
        for k,v in var_dict.items():
            var_dict[k]=[v]
        df=pd.DataFrame(var_dict)
        df.reset_index(inplace=True)
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
    
@dataclass
class Branch(DataFrameAdapter):
    name:str
    commits:list[str]
@dataclass
class File(DataFrameAdapter):
    name:str
    size:str
    path:str
    hash_string:str
    def __eq__(self, value):
        if not isinstance(value,File):
            raise TypeError(f"Cannot compare type File with {type(value)}")
        return value.hash_string==self.hash_string
    def __hash__(self):
        return self.hash_string.__hash__()
@dataclass
class Folder(DataFrameAdapter):
    name:str
    content:dict[str,Union[File,'Folder']]
    hash_string:str
    path:str
    def __eq__(self, value):
        if not isinstance(value,Folder):
            raise TypeError(f"Cannot compare type Folder with {type(value)}")
        return value.hash_string==self.hash_string
    def __hash__(self):
        return self.hash_string.__hash__()
    
    def get_dataframe(self):
        df_dict:dict[str|int,list]=dict()
        df_dict["folder"]=[self.base.name]
        df_dict["hash_string"]=[self.base.hash_string]
        df_dict["size"]=[pd.NA]
        df_dict["file"]=[pd.NA]
        df_dict["contained_folder"]
        df=pd.DataFrame()
        for k,v in self.content.items():
            df_dict["hash_string"].append(v.hash_string)
            if isinstance(v,Folder):
                nd=v.get_dataframe()
                df_dict["size"].append(pd.NA)
                df_dict["folder"].append(k)
                df_dict["file"].append(pd.NA)
                df=pd.concat([df,nd])
            else:
                df_dict["folder"].append(self.name)
                df_dict["file"].append(k)
                df_dict["size"].append(v.size)
        return pd.concat([df,pd.DataFrame(df_dict)])

    def get_dataframe_dict(self,level:int)->dict[str]:
        df_dict:dict[str|int,list]=dict()
        df_dict["hash_string"]=list()
        df_dict["size"]=list()
        level+=1
        df_dict[level]=list()
        for k,v in self.content.items():
            df_dict[level].append(k)
            df_dict["hash_string"].append(v.hash_string)
            if isinstance(v,Folder):
                nd=v.get_dataframe_dict(level)
                df_dict["hash_string"].extend(nd["hash_string"])
                df_dict["size"].extend(nd["size"])
                for k in nd.keys():
                    if k not in df_dict:
                        df_dict[k]=nd[k]
            else:
                df_dict["size"].append(v.size) 
        return df_dict

class TreeStructure(DataFrameAdapter):
    def __init__(self,content:Iterable[Union[Folder,File]],hash:str):
        self.base:Folder=Folder(name="root",content=dict(),path="",hash_string=hash)
        for c in content:
            c.path=Path(self.base.name).joinpath(c.name).as_posix()
            self.base.content[c.name]=c
    #Folder->contained_folder/file structure dataframe
    def get_dataframe(self):
        pass
    
    def get_treemap(self):
        dat_dict:dict[str,Union[Folder,File]]=dict(parent=[],child=[],name=[],type=[])
        for path,o in self.walk():
            dat_dict["parent"].append(path if path else "root")
            dat_dict["name"].append(o.name)

            dat_dict["child"].append(f"{path}/{o.name}" if path else o.name)
            dat_dict["type"].append("folder" if isinstance(o,Folder) else "file")

        return dat_dict
    
    def walk(self,files_only:bool=False,dirs_only:bool=False)->Generator[tuple[str,Union[Folder,File]],None,None]:
        if files_only and dirs_only:
            raise ValueError("Arguments files_only and dirs_only must be mutually exclusive")
        objects=self.base.content.values()
        folders_to_visit:list[Folder]=[]
        end=False
        path=""
        for o in objects:
            if isinstance(o,File):
                if not dirs_only:
                    yield (path,o)
            else:
                folders_to_visit.append(o)
                if not files_only:
                    yield (path,o)
        while not end:
            fold=folders_to_visit.pop()
            path=f"{path}/{fold.name}" if path else fold.name
            for o in fold.content.values():
                if isinstance(o,Folder):
                    folders_to_visit.append(o)
                    if not files_only:
                        yield (path,o)
                elif isinstance(o,File) and not dirs_only:
                    yield (path,o)
            end = not folders_to_visit
            
            
    def walk_folder(self,name:str,files_only:bool=False,dirs_only:bool=False)->Generator[Union[Folder,File],None,None]:
        if files_only and dirs_only:
            raise ValueError("Arguments files_only and dirs_only must be mutually exclusive")
        if name not in self.base.content:
            raise ObjectNotInTreeError(f"Object {name} not found among objects {' '.join(self.base.content.keys())}")
        obj=self.base.content[name]
        if isinstance(obj,Folder):
            end=False
            folders_to_visit:list[Folder]=[obj]
            while not end:
                fold=folders_to_visit.pop()
                for o in fold.content.values():
                    if isinstance(o,Folder):
                        folders_to_visit.append(o)
                        if not files_only:
                            yield o
                    elif isinstance(o,File) and not dirs_only:
                        yield o
                end = not folders_to_visit
        else:
            yield obj
    
    def find(self,name:str,type:Optional[Literal["file","folder"]]=None)->Generator[Union[File,Folder],None,None]:
        folder_only=False
        file_only=False
        if type:
            if type=="file":
                file_only=True
            elif type=="folder":
                folder_only=True
            else:
                raise TypeError("The only accepted type values are 'file' and 'folder'")
        for o in self.walk(file_only,folder_only):
            if o.name==name:
                yield o
                
    def get(self,path:str)->Union[File,Folder]:
        parts=Path(path).parts
        ret_object=None
        to_explore:list[Folder]=[self.base]

        for p in parts:
            obj=to_explore.pop()
            if p in obj.content:
                if isinstance(obj.content[p],Folder):
                    to_explore.append(obj.content[p])
                ret_object=obj.content[p]
            else:
                raise ObjectNotInTreeError(f"Path {path} is not part of this tree")
            
        return ret_object