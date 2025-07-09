from typing import Generator,Iterable
from src._internal import TreeStructure,File,Folder
from repository_miner import RepoMiner,GitCmdError
from repository_miner.data_typing import Blob,Tree,CommitInfo
from pathlib import Path
import pandas as pd
import truck_factor_gdeluisi.main as tf_calculator
from src.utility.helper import get_dataframe
from os import cpu_count
from math import ceil,floor
from concurrent.futures import ThreadPoolExecutor,ProcessPoolExecutor
from functools import partial
import dash_bootstrap_components as dbc
from dash import html
max_worker = min(32,cpu_count())

def build_tree_structure(miner:RepoMiner,commit_sha:str,path_filter:Iterable=set())->TreeStructure:
    t=miner.tree(commit_sha)
    tree = TreeStructure(hash=t.hash,content=[])
    for o in t.traverse():
        obj=None
        if o.path not in path_filter:
            continue
        if isinstance(o,Blob):
            obj=File(name=o.name,size=o.size,hash_string=o.hash)
        else:
            obj=Folder(name=Path(o.path).name,content=dict(),hash_string=o.hash)
        tree.build(path=o.path,new_obj=obj)
    return tree

def retrieve_SATDs(miner:RepoMiner,satd_highlighters:Iterable[str])->dict[str,dict[int,str]]:
    reg=f'\"[^a-zA-Z0-9_]+\\s*({"|".join(satd_highlighters)}).+\"'
    lines=[]
    try:
        lines=miner.git.grep(["-E","-n","-o","-I",reg])
    except GitCmdError:
        return dict()
    satds:dict[str,dict[int,str]]=dict()
    for line in lines.split('\n'):
        try:
            path,n,satd=line.split(":",2)
            satd=satd.strip()
            res=satds.get(path,{})
            res[n]=satd
            satds[path]=res
        except ValueError:
            print(line)
    return satds

def retrieve_contribution_data(repo_path:str)->tuple[pd.DataFrame,int]:
    contributions=tf_calculator.compute_DOA(tf_calculator.create_contribution_dataframe(repo_path,only_of_files=False))
    tf_contributions=tf_calculator.filter_files_of_interest(contributions)
    tr_fa=tf_calculator.compute_truck_factor_from_contributions(tf_contributions)
    return (contributions,tr_fa)

def parallel_commit_retrievial(rp:RepoMiner)->list[CommitInfo]:
    no_commits=rp.n_commits()
    c_slice=ceil(no_commits/max_worker)
    return_commits=[]
    tasks=[]
    with ThreadPoolExecutor(max_workers=max_worker) as executor:
        for i in range(max_worker):
            tasks.append(executor.submit(rp.retrieve_commit_list,max_count=c_slice,skip=i*c_slice,merges=True))
    for c_list in tasks:
        res=c_list.result()
        if res:
            return_commits.extend(res)
    return return_commits

def create_info_card_columns(texts:dict,icons:dict)->list:
    cols=[]
    fraction=ceil(12/len(texts))
    width=max(fraction,1)
    for title,text in texts.items():
        icon=""
        if title in icons:
            icon = icons[title]
        cols.append(dbc.Col(
                    [
                            dbc.Card([
                                    dbc.CardHeader([icon,title],class_name="fw-bold h5 text-start"),
                                    dbc.CardBody(children=[text],class_name="h5 text-center"),
                            ],class_name="m-2")
                    ]
            ,width=width,align="start"))
    return cols