from typing import Generator
from src._internal import TreeStructure,File,Folder
from repository_miner import RepoMiner
from repository_miner.data_typing import Blob,Tree
from pathlib import Path

def build_tree_structure(miner:RepoMiner,commit_sha:str)->TreeStructure:
    t=miner.tree(commit_sha)
    tree = TreeStructure(hash=t.hash,content=[])
    for o in t.traverse():
        obj=None
        if isinstance(o,Blob):
            obj=File(name=o.name,size=o.size,hash_string=o.hash)
        else:
            obj=Folder(name=Path(o.path).name,content=dict(),hash_string=o.hash)
        tree.build(path=o.path,new_obj=obj)
    return tree
