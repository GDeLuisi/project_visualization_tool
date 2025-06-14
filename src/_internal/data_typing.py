from  dataclasses import dataclass,field
from datetime import date
from time import strptime
from .exceptions import ObjectNotInTreeError,PathNotAvailableError
from typing import Literal,get_args,Iterable,Optional,Union,Generator,Callable
import json
from repository_miner.data_typing import CommitInfoImpl
from src.utility.helper import get_dataframe
import pandas as pd
from pathlib import Path
# ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]
ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]
CONFIG_FOUND=False
config_path=Path(__file__).parent.joinpath("info","ext.json")
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

class RetrieveStrategy():
    def get_source(self,id:str)->list[str]:
        pass
    

# {'commit': '1c85669eb58fc986d43eb7c878e03cb58fb4883d', 'abbreviated_commit': '1c85669', 'tree': 'c6a6edfde2001a68e123c724625faf7599f82371', 'abbreviated_tree': 'c6a6edf', 'parent': 'efe6fba7d02ad06bec603b57f2e5115b7ccd31d8', 'abbreviated_parent': 'efe6fba', 'refs': 'HEAD -> development, origin/development', 'encoding': '', 'subject': 'optimized truck factor function', 'sanitized_subject_line': 'optimized-truck-factor-function', 'body': '', 'commit_notes': '', 'verification_flag': 'N', 'signer': '', 'signer_key': '', 'author': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}, 'commiter': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}}
@dataclass
class SATD():
    satdID: int
    commitID: str
    content: str
    category: str
    file: str
    
@dataclass
class Author():
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
    def __repr__(self):
        return  f"Name: {self.name} , Email: {self.email} , Commits: {self.commits_authored}"

@dataclass
class File():
    name:str
    size:int
    hash_string:str
    def get_source(self,ret_strategy:RetrieveStrategy)->list[str]:
        return ret_strategy.get_source(self.hash_string)
    def __eq__(self, value):
        if not isinstance(value,File):
            raise TypeError(f"Cannot compare type File with {type(value)}")
        return value.hash_string==self.hash_string
    def __hash__(self):
        return self.hash_string.__hash__()
    

@dataclass
class Folder():
    name:str
    content:dict[str,Union[File,'Folder']]
    hash_string:str
    def __eq__(self, value):
        if not isinstance(value,Folder):
            raise TypeError(f"Cannot compare type Folder with {type(value)}")
        return value.hash_string==self.hash_string
    def __hash__(self):
        return self.hash_string.__hash__()
    
    def get_size(self)->int:
        tot_size=0
        for k,v in self.content.items():
            if isinstance(v,File):
                tot_size+=v.size
            else:
                tot_size+=v.get_size()
        return tot_size
    
    def get_dataframe(self):
        size=self.get_size()
        df=pd.DataFrame(dict(size=[size],name=[self.name],hash_string=[self.hash_string]))
        for v in self.content.values():
            df=pd.concat([df,get_dataframe(v)],ignore_index=True).reset_index(drop=True)
        return df

class TreeStructure():
    def __init__(self,hash:str,content:Optional[Iterable[Union[Folder,File]]]=None):
        self.base:Folder=Folder(name="",content=dict(),hash_string=hash)
        self.hash=hash
        if content:
            for c in content:
                self.base.content[c.name]=c
    #Folder->contained_folder/file structure dataframe
    def get_dataframe(self):
        return self.base.get_dataframe()
    
    def get_treemap(self)->dict[str,list[str]]:
        dat_dict:dict[str,list[str]]=dict(parent=[],child=[],name=[],type=[],id=[])
        for path,o in self.walk():
            dat_dict["parent"].append(path if path else "")
            dat_dict["name"].append(o.name)
            dat_dict["id"].append(o.hash_string)
            dat_dict["child"].append(f"{path}/{o.name}" if path else o.name)
            dat_dict["type"].append("folder" if isinstance(o,Folder) else "file")
        return dat_dict
    
    def walk(self,files_only:bool=False,dirs_only:bool=False)->Generator[tuple[str,Union[Folder,File]],None,None]:
        if files_only and dirs_only:
            raise ValueError("Arguments files_only and dirs_only must be mutually exclusive")
        objects=self.base.content.values()
        folders_to_visit:list[tuple[str,Folder]]=[]
        
        end=True
        path=""
        for o in objects:
            if isinstance(o,File):
                if not dirs_only:
                    yield (path,o)
            else:
                folders_to_visit.append((path,o))
                if not files_only:
                    yield (path,o)
                end=False
        while not end:
            path,fold=folders_to_visit.pop()
            path=f"{path}/{fold.name}" if path else fold.name
            for o in fold.content.values():
                if isinstance(o,Folder):
                    folders_to_visit.append((path,o))
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
        for path,o in self.walk(file_only,folder_only):
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
    
    def build(self,path:str,new_obj:Union[File,Folder],mkdir:bool=True):
        if not isinstance(new_obj,(File,Folder)):
            raise TypeError("Object must be of type or subtype of File or Folder")
        if not path:
            raise ValueError("Nonetype or empty string are not amissible paths")
        parts=Path(path).parts
        to_explore:list[Folder]=[self.base]
        num_parts=len(parts)
        last_folder=None
        for i,p in enumerate(parts,1):
            obj=to_explore.pop()
            last_folder=obj
            if p in obj.content:
                if isinstance(obj.content[p],Folder) and not num_parts==i:
                    to_explore.append(obj.content[p])
                else:
                    raise PathNotAvailableError("Either path is not a sequence of folder or path already used")
                
            else:
                if mkdir and not num_parts==i:
                    f=Folder(name=p,content=dict(),hash_string="")
                    obj.content[p]=f
                    to_explore.append(f)
                elif num_parts==i:
                    if not last_folder:
                        self.base.content[new_obj.name]=new_obj
                        return
                    last_folder.content[p]=new_obj
                else:
                    raise ObjectNotInTreeError("Path not reachable")
                
    @staticmethod
    def build_tree(hash:str,path:str,new_obj:Union[File,Folder],mkdir:bool=True)->'TreeStructure':
        tree = TreeStructure(hash=hash)
        if not isinstance(new_obj,(File,Folder)):
            raise TypeError("Object must be of type or subtype of File or Folder")
        if not path:
            raise ValueError("Nonetype or empty string are not amissible paths")
        parts=Path(path).parts
        to_explore:list[Folder]=[tree.base]
        num_parts=len(parts)
        last_folder=None
        for i,p in enumerate(parts,1):
            obj=to_explore.pop()
            last_folder=obj
            if p in obj.content:
                if isinstance(obj.content[p],Folder) and not num_parts==i:
                    to_explore.append(obj.content[p])
                else:
                    raise PathNotAvailableError("Either path is not a sequence of folder or path already used")
                
            else:
                if mkdir and not num_parts==i:
                    f=Folder(name=p,content=dict(),hash_string="")
                    obj.content[p]=f
                    to_explore.append(f)
                elif num_parts==i:
                    if not last_folder:
                        tree.base.content[new_obj.name]=new_obj
                        return
                    last_folder.content[p]=new_obj
                else:
                    raise ObjectNotInTreeError("Path not reachable")
        return tree