import pydriller as git
import pydriller.metrics.process.contributors_count as contr
import pydriller.metrics.process.history_complexity as history
import pydriller.metrics.process.commits_count as comcnt
from .data_typing import Author
from typing import Optional,Generator,Union,Iterable
from pathlib import Path
from datetime import datetime
from git import Git,Repo,Blob,Commit
from io import BytesIO
import re
import os
from math import log1p
from threading import Thread,Lock
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from time import monotonic,sleep
from logging import getLogger

logger=getLogger("Repo Miner")
#TODO implemente a threaded version for optimization
class RepoMiner():
    def __init__(self,repo_path:Union[Path,str]):
        self.repo_path=repo_path
        if isinstance(repo_path,Path):
            self.repo_path=repo_path.as_posix()
        self.repo=Repo(self.repo_path)
        self.commit_list=list(self.repo.iter_commits())
        

    def get_commits_hash(self,since:Optional[datetime]=None,to:Optional[datetime]=None)->Generator[str,None,None]:
        repo=git.Repository(path_to_repo=self.repo_path,since=since,to=to)
        return (commit.hash for commit in repo.traverse_commits())
    
    def get_commits_between(self,from_commit:str,to_commit:str)->Generator[str,None,None]:
        repo=git.Repository(path_to_repo=self.repo_path,from_commit=from_commit,to_commit=to_commit)
        return (commit.hash for commit in repo.traverse_commits())
    
    def get_all_authors(self)->set[Author]:
        authors:set[Author]=set((Author(commit.author.email,commit.author.name) for  commit in self.commit_list))
        return authors
    
    def get_file_author(self,file:str)->Author:
        repo=git.Repository(path_to_repo=self.repo_path,only_no_merge=True,filepath=file)
        cm_list=list(repo.traverse_commits())
        author=Author(cm_list[0].author.email,cm_list[0].author.name)
        return author

    def get_author_commits(self,author_name:str)->Generator[str,None,None]:
        repo=git.Repository(path_to_repo=self.repo_path,only_authors=[author_name])
        return (commit.hash for commit in repo.traverse_commits())

    def get_file_authors(self,file:str)->set[Author]:
        repo=git.Repository(path_to_repo=self.repo_path,only_no_merge=True,filepath=file)
        authors:set[Author]=set((Author(commit.author.email,commit.author.name) for  commit in repo.traverse_commits()))
        return authors
    
    def get_commit(self,commit_hash:str)->git.Commit:
        repo=git.Repository(path_to_repo=self.repo_path,single=commit_hash)
        return list(repo.traverse_commits())[0]

    def get_last_modified(self,commit:str):
        git_repo=git.Git(self.repo_path)
        return git_repo.get_commits_last_modified_lines(git_repo.get_commit(commit))
    #TODO include option to use multiple filenames
    def get_source_code(self,file:Union[str,Path],commit:Optional[str]=None)->list[str]:
        text=[]
        file_path=file
        if isinstance(file,str):
            file_path=Path(file)
        git_repo=Repo(self.repo_path)
        target_commit=git_repo.commit(commit)
        tree=target_commit.tree
        try:
            relative_path=file_path.relative_to(self.repo_path)
        except ValueError:
            logger.critical(f"File {file_path.as_posix()} not under repo directory")
            raise FileNotFoundError("File not under repo directory")
        else:
            f=tree.join(relative_path.as_posix())
            if not isinstance(f,Blob):
                logger.critical(f"Path {file_path.as_posix()} is not a file")
                raise FileNotFoundError("Not a file")
            with BytesIO(f.data_stream.read()) as fl:
                text=re.split(string=fl.read().decode(),pattern=r'\r\n|\n|\r')
        return text
    
    def calculate_DL(self,input_tuple:tuple[Author,list[Commit]])->int:
        author,commit_list=input_tuple
        contribution=0
        for commit in commit_list:
            ath=commit.author
            if ath.name==author.name and ath.email==author.email:
                contribution+=1
        return contribution
    
    def _calculate_DOA(self,input_tuple:tuple[Author,list[Commit]])->tuple[Author,float]:
        author,commit_list=input_tuple
        # commit_list=list(commit_list)
        creation_commit=commit_list[0] if commit_list else None
        FA=0
        DL=0
        if creation_commit and Author(creation_commit.author.email,creation_commit.author.name) == author:
            FA=1
        DL=self.calculate_DL((author,commit_list))
        logger.error(f"Calculating DOA for {str(author)}")
        AC:int=abs(len(commit_list)-DL)
        DOA=3.293+1.098*FA+0.164*DL-0.321*log1p(AC)
        return (author,DOA)
    
    def calculate_file_DOA(self,input_tuple:tuple[tuple[str, list[Commit]], set[Author]])->tuple[str,dict[Author,float]]:
        author_doa:dict[Author,float]=dict()
        file_tuple,authors=input_tuple
        filepath,commit_list=file_tuple
        commit_list=list(commit_list)
        logger.error(f"Checking {filepath} with {len(commit_list)}")
        tuple_list=map(lambda item:(item,commit_list),authors)
        
        with ThreadPoolExecutor() as executor:
            results=executor.map(self._calculate_DOA,tuple_list)
        for result in results:
            author,doa=result
            author_doa[author]=doa
        return (filepath,author_doa)
    
    #FIXME need to be optimized avaragae of 18s of execution
    def get_truck_factor(self,doa_threshold:float=0.75)->tuple[int,dict[Author,list[str]]]:
        tree=self.repo.tree()
        authors=self.get_all_authors()
        author_files_counter:dict[Author,list[str]]=dict([(author,[]) for author in authors])
        files_author_count:dict[str,int]=dict()
        file_relative_commit:dict[str,list[Commit]]=dict()
        orphans=0
        tf=0
        tot_files=0
        for commit in self.commit_list:
            m_files=commit.stats.files.keys()
            for file in m_files:
                if not file in file_relative_commit:
                    file_relative_commit[file]=[]
                file_relative_commit[file].append(commit)
                files_author_count[file]=0
        tuple_list=map(lambda item:(item,authors),file_relative_commit.items())
        logger.error(file_relative_commit.keys())
        # logger.error(tuple_list)
        # print(len(tuple_list),tuple_list)
        with ThreadPoolExecutor() as executor:
            results=executor.map(self.calculate_file_DOA,tuple_list)
        for result in results:
            file,doas=result
            for author,doa in doas.items():
                max_doa=sorted(doas.values(),reverse=True)[0]
                if float(doa/max_doa)>= doa_threshold:
                    author_files_counter[author].append(file)
                    files_author_count[file]+=1
        author_sorted_list=sorted(((k,v) for k,v in author_files_counter.items()),key=lambda item:len(item[1]),reverse=True)
        logger.debug("Author sorted DOA list",extra=dict(author_list=author_sorted_list))
        i=int(0)
        while orphans <= int(tot_files/2):
            author,fs=author_sorted_list[i]
            i+=1
            for f in fs:
                files_author_count[f]-=1
                if files_author_count[f]==0:
                    orphans+=1
                print(orphans,i)
                if orphans > int(tot_files/2):
                    tf=i
                    break
        return (tf,author_files_counter)
