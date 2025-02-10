import pydriller as git
import pydriller.metrics.process.contributors_count as contr
import pydriller.metrics.process.history_complexity as history
import pydriller.metrics.process.commits_count as comcnt
from .data_typing import Author,CommitInfo
from time import strptime,mktime
from typing import Optional,Generator,Union,Iterable
from pathlib import Path
from datetime import date
from git import Git,Repo,Blob,Commit
from io import BytesIO
import re
import os
from math import log1p
from threading import Thread,Lock
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from logging import getLogger
from functools import cached_property
import json
logger=getLogger("Repo Miner")
#FIXME restructure whole class with recent optimization 
class RepoMiner():
    def __init__(self,repo_path:Union[Path,str]):
        self.repo_path=repo_path
        if isinstance(repo_path,Path):
            self.repo_path=repo_path.as_posix()
        self.repo=Repo(self.repo_path)
        self.git_repo=self.repo.git
        self.commits_info:dict[str,CommitInfo]=dict()
        self.authors:set[Author]=set()
        self.update()
        
    def update(self,fetch_all:bool=False,pull_all:bool=False):
        if fetch_all:
            self.git_repo.fetch("--all")
        if pull_all:
            self.git_repo.pull("--all")
        # "--all","--name-only","--pretty=format:|{'commit': '1c85669eb58fc986d43eb7c878e03cb58fb4883d', 'abbreviated_commit': '1c85669', 'tree': 'c6a6edfde2001a68e123c724625faf7599f82371', 'abbreviated_tree': 'c6a6edf', 'parent': 'efe6fba7d02ad06bec603b57f2e5115b7ccd31d8', 'abbreviated_parent': 'efe6fba', 'refs': 'HEAD -> development, origin/development', 'encoding': '', 'subject': 'optimized truck factor function', 'sanitized_subject_line': 'optimized-truck-factor-function', 'body': '', 'commit_notes': '', 'verification_flag': 'N', 'signer': '', 'signer_key': '', 'author': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}, 'commiter': {'name': 'Gerardo De Luisi', 'email': 'deluisigerardo@gmail.com', 'date': 'Sat, 8 Feb 2025 14:21:03 +0100'}}
        files:list[str]=self.git_repo.log("--all","--name-only","--pretty=format:|").split('|')
        files=list(reversed([re.split(string=file.strip('\n\r'),pattern=r'\r\n|\n|\r') for file in files][1:]))
        logs=re.split(string=self.git_repo.log("--all","--no-merges",'--pretty=format:{"commit": "%H","abbreviated_commit": "%h","tree": "%T","abbreviated_tree": "%t","parent": "%P","abbreviated_parent": "%p","refs": "%D","encoding": "%e","subject": "%s","sanitized_subject_line": "%f","body": "%b","commit_notes": "%N","verification_flag": "%G?","signer": "%GS","signer_key": "%GK","author": {"name": "%aN","email": "%aE","date": "%aD"},"commiter": {"name": "%cN","email": "%cE","date": "%cD"}}'),pattern=r'\r\n|\n|\r')
        logs=reversed([json.loads(log) for log in logs])
        author_dict:dict[Author,dict[str,list]]=dict()
        for i,log in enumerate(logs):
            auth=Author(log["author"]["email"],log["author"]["name"])
            if not auth in author_dict:
                author_dict[auth]=dict(files=set(),commits=list())
            author_dict[auth]["files"].update(files[i])
            author_dict[auth]["commits"].append(log["commit"])
            
            self.commits_info[log["commit"]]=CommitInfo(
                                                author_email=log["author"]["email"],
                                                author_name=log["author"]["name"],
                                                commit_hash=log["commit"],
                                                abbr_hash=log["abbreviated_commit"],
                                                tree=log["tree"],
                                                refs=log["refs"],
                                                subject=log["subject"],
                                                date=date.fromtimestamp(mktime(strptime(log["author"]["date"],"%a, %d %b %Y %H:%M:%S %z"))),
                                                parent=log["parent"],
                                                files=files[i])
        for author,v in author_dict.items():
            author.files_modifed=v["files"]
            author.commits_authored=v["commits"]
            self.authors.add(author)
        # self.commit_list=[self.repo.commit(hash) for hash in self.commit_list_hashes]
        # [commit.stats for commit in self.commit_list]
        # self.truck_factor=self.get_truck_factor()[0]
    
    def get_file_authors(self,fileapath:Union[str,Path])->Generator[Author,None,None]:
        path=fileapath
        if isinstance(fileapath,str):
            path=Path(fileapath)
        path=path.relative_to(self.repo_path)
        logger.debug(f"Relative Path {path.as_posix()}")
        for author in self.authors:
            if path.as_posix() in author.files_modifed:
                logger.debug(f"Found {path.as_posix()} in {str(author)}")
                yield author
    
    def get_commit(self,commit_hash:str)->CommitInfo:
        return self.commits_info[commit_hash]

    def get_last_modified(self,commit:str)->Generator[CommitInfo,None,None]:
        git_repo=git.Git(self.repo_path)
        for k in git_repo.get_commits_last_modified_lines(git_repo.get_commit(commit)).keys():
            yield self.commits_info[k]
    def get_author_commits(self,name:str,email:str)->list[CommitInfo]:
        for author in self.authors:
            if name and email and author.name == name and author.email ==email:
                return author.commits_authored
        return []
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
    
    def _calculate_DL(self,input_tuple:tuple[Author,list[CommitInfo]])->int:
        author,commit_list=input_tuple
        contribution=0
        for commit in commit_list:
            name,email=commit.author_name,commit.author_email
            if name==author.name and email==author.email:
                contribution+=1
        return contribution
    
    def _calculate_DOA(self,input_tuple:tuple[Author,list[CommitInfo]])->tuple[Author,float]:
        author,commit_list=input_tuple
        creation_commit=commit_list[0] if commit_list else None
        FA=0
        DL=0
        logger.debug(f"Creation commit {creation_commit}")
        if creation_commit and Author(creation_commit.author_email,creation_commit.author_name) == author:
            FA=1
        DL=self._calculate_DL((author,commit_list))
        logger.debug(f"Calculating DOA for {str(author)}")
        AC:int=abs(len(commit_list)-DL)
        DOA=3.293+1.098*FA+0.164*DL-0.321*log1p(AC)
        return (author,DOA)
    
    def calculate_file_DOA(self,input_tuple:tuple[tuple[str, list[CommitInfo]], set[Author]])->tuple[str,dict[Author,float]]:
        author_doa:dict[Author,float]=dict()
        # print(author)
        file_tuple,authors=input_tuple
        filepath,commit_list=file_tuple
        logger.debug(f"Checking {filepath} with {len(commit_list)}")
        # print(f"Checking {filepath} with {len(commit_list)}")
        tuple_list=map(lambda item:(item,commit_list),authors)
        with ThreadPoolExecutor() as executor:
            results=executor.map(self._calculate_DOA,tuple_list)
        for result in results:
            # print(result)
            author,doa=result
            author_doa[author]=doa
        return (filepath,author_doa)
    
    def get_file_commits(self,commit_list:Optional[list[CommitInfo]]=None)->dict[str,list[Commit]]:
        c_list=commit_list if commit_list else self.commits_info
        file_relative_commit:dict[str,list[Commit]]=dict()
        for commit in c_list:
            for file in commit.files:
                file_relative_commit[file].append(commit)
        return file_relative_commit

    def get_truck_factor(self,doa_threshold:float=0.75)->tuple[int,dict[Author,list[str]]]:
        authors=self.authors
        author_files_counter:dict[Author,list[str]]=dict([(author,[]) for author in authors])
        files_author_count:dict[str,int]=dict()
        file_relative_commit:dict[str,list[Commit]]=dict()
        orphans=0
        tf=0
        tot_files=0
        for commit in self.commits_info.values():
            for file in commit.files:
                if file not in file_relative_commit:
                    file_relative_commit[file]=[]
                file_relative_commit[file].append(commit)
                files_author_count[file]=0
        tot_files=len(files_author_count.keys())
        # print(file_relative_commit)
        tuple_list=map(lambda item:(item,authors),file_relative_commit.items())
        with ThreadPoolExecutor() as executor:
            results=executor.map(self.calculate_file_DOA,tuple_list)
        for result in results:
            # print(result)
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
                # print(orphans,i)
                if orphans > int(tot_files/2):
                    tf=i
                    break
        return (tf,author_files_counter)
    
