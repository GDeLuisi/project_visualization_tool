import pydriller as git
import pydriller.metrics.process.contributors_count as contr
import pydriller.metrics.process.history_complexity as history
import pydriller.metrics.process.commits_count as comcnt
from .data_typing import Author,CommitInfo,check_extension,Branch,File,Folder,TreeStructure,RetrieveStrategy
from time import strptime,mktime
from typing import Optional,Generator,Union,Iterable,get_args
from pathlib import Path
from datetime import date
from git import Git,Repo,Blob,Commit,exc
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

class GitRetrivialStrategy(RetrieveStrategy):
    def __init__(self,repo_path:Union[Path,str]):
        self.repo_path=repo_path
        if isinstance(repo_path,Path):
            self.repo_path=repo_path.as_posix()
        self.git=Git(self.repo_path)
    def get_source(self, id:str)->list[str]:
        try:
            if self.git.cat_file("-t",id) != "blob":
                raise TypeError(f"Hexsha {id} in not a blob")
        except exc.GitCommandError:
            raise FileNotFoundError("Couldn't retrieve the object")
        return re.split(string=self.git.cat_file("-p",id),pattern=r"\r\n|\r|\n")
        

class RepoMiner():
    COMMIT_PRETTY_FORMAT='--pretty=format:{"commit": "%H","abbreviated_commit": "%h","tree": "%T","abbreviated_tree": "%t","parent": "%P","abbreviated_parent": "%p","refs": "%D","encoding": "%e","subject": "%s","sanitized_subject_line": "%f","commit_notes": "%N","verification_flag": "%G?","signer": "%GS","signer_key": "%GK","author": {"name": "%aN","email": "%aE","date": "%aD"},"commiter": {"name": "%cN","email": "%cE","date": "%cI"}}|'
    def __init__(self,repo_path:Union[Path,str]):
        self.repo_path=repo_path
        if isinstance(repo_path,Path):
            self.repo_path=repo_path.as_posix()
        self.repo_lock=Lock()
        self.repo=Repo(self.repo_path)
        self.git_repo=self.repo.git
        self.tree=None
        self.tree=self.get_dir_structure()
        # self.update()
        #"--no-merges","--no-commit-header",f"--max-count={max_count}",'--pretty=format:{"commit": "%H","abbreviated_commit": "%h","tree": "%T","abbreviated_tree": "%t","parent": "%P","abbreviated_parent": "%p","refs": "%D","encoding": "%e","subject": "%s","sanitized_subject_line": "%f","body": "%b","commit_notes": "%N","verification_flag": "%G?","signer": "%GS","signer_key": "%GK","author": {"name": "%aN","email": "%aE","date": "%aD"},"commiter": {"name": "%cN","email": "%cE","date": "%cD"}}',last_revision),pattern=r'\r\n|\n|\r'
    def _load_commits_date_range(self,start_date:Optional[date]=None,end_date:Optional[date]=None)->list[str]:
        # start,end = start_date,end_date if start_date>end_date else end_date,start_date
        arglist=[]
        raise_exc=False
        try:
            if start_date > end_date:
                raise_exc=True
        except TypeError:
            pass
        finally:
            if raise_exc:
                raise SyntaxError("Start date cannot come after end date")
            start_string=f"--since={start_date.isoformat()}" if start_date else None
            end_string=f"--before={end_date.isoformat()}" if end_date else None
            if start_string:
                arglist.append(start_string)
            if end_string:
                arglist.append(end_string)
            return arglist
                
    def _load_commits_commit_range(self,start_commit:Optional[str]=None,end_commit:Optional[str]=None,deafult:Optional[str]="HEAD")->str:
        # start,end = start_date,end_date if start_date>end_date else end_date,start_date
        if not deafult:
            deafult=""
        commit_range=""
        commit_range=commit_range+start_commit if start_commit else ""
        if end_commit:
            commit_range=commit_range+".."+end_commit if commit_range else end_commit
        elif not start_commit:
            commit_range=deafult
        else:
            commit_range=commit_range+f"..{deafult}"
        return commit_range
    
    def _rev_list(self,only_branch:Optional[str]=None,max_count:Optional[int]=None,no_merges:bool=True,count_only:bool=False,from_commit:Optional[str]=None,to_commit:Optional[str]=None,from_date:Optional[date]=None,to_date:Optional[date]=None)->list[str]:
        arglist=[]
        commit_range=self._load_commits_commit_range(start_commit=from_commit,end_commit=to_commit)
        arglist.append(commit_range)
        arglist.extend(self._load_commits_date_range(from_date,to_date))
        if max_count:
            arglist.append(f"--max-count={max_count}")
        if count_only:
            arglist.append("--count")
        if no_merges:
            arglist.append("--no-merges")
        if only_branch:
            arglist.append("--first-parent")
        else:
            arglist.append("--all")
        logger.debug("Calling rev-list with the following args",extra={"arguments":arglist})
        with self.repo_lock:
            commits=re.split(string=self.git_repo.rev_list(arglist),pattern=r'\r\n|\n|\r')
        return commits
    def _log(self,arglist:list[str],follow:bool=False)->Generator[list[CommitInfo],None,None]:
        finished=False
        while not finished:
            with self.repo_lock:
                logs_uf=re.split(string=self.git_repo.log(arglist),pattern=r'\|\r\n|\|\n|\|\r|\|')[:-1]
            # logger.debug("Loaded commits",extra={"commits":logs})
            if not logs_uf or not logs_uf[0] :
                logger.debug("Finished Loading")
                finished=True
                return []
            logs:list[str]=[]
            try:
                for log in logs_uf:
                    log=re.sub(string=log,pattern=r'\'|\r\n|\n|\r',repl=" ")
                    l=re.sub(string=log,pattern=r' \"([^"]+)\"[\"|\s](\,\")?',repl=lambda m: m.group(1)+'\"'+m.group(2) if m.group(2)  else ' ')
                    logs.append(json.loads(l))
            except json.JSONDecodeError as e:
                # logger.critical(str(e))
                logger.critical("Something went wrong with commits loading process")
                logger.critical(str(e))
                logger.critical(f"Faulty object original {log}")
                logger.critical(f"Faulty object {l}")
                exit(1)
            last_revision=logs[0]["commit"].split(" ")[0]
            commit_list:list[CommitInfo]=[]
            for log in logs:
                commit_info=CommitInfo(
                                                    author_email=log["author"]["email"],
                                                    author_name=log["author"]["name"],
                                                    commit_hash=log["commit"],
                                                    abbr_hash=log["abbreviated_commit"],
                                                    tree=log["tree"],
                                                    refs=log["refs"],
                                                    subject=log["subject"],
                                                    date=date.fromtimestamp(mktime(strptime(log["author"]["date"],"%a, %d %b %Y %H:%M:%S %z"))),
                                                    parent=log["parent"],
                                                    files=[])
                commit_list.append(commit_info)
            next_revision=commit_info.parent.strip().split(" ")[0]
            yield commit_list
            if follow:
                file=arglist.pop()
                flag=arglist.pop()
                rev=arglist.pop(0)
                arglist.insert(0,next_revision)
                arglist.append(flag)
                arglist.append(file)
            else:
                rev=arglist.pop(0)
                if ".." in rev:
                    start,pr_end=rev.split("..")
                    next_revision=f"{next_revision}...{pr_end}"
                if "--" in rev:
                    arglist.insert(0,rev)
                arglist.insert(0,next_revision)
                
            logger.debug(f"Reloaded arglist {arglist}")
            finished = not next_revision or next_revision==last_revision or next_revision==rev
            
    
    def lazy_load_commits(self,no_merges:bool=True, max_count:int=None,filepath:Optional[Union[str,Path]]=None,relative_path:Optional[Union[str,Path]]=None,start_date:Optional[date]=None,end_date:Optional[date]=None,start_commit:Optional[str]=None,end_commit:Optional[str]=None,author:Optional[str]=None)->Generator[list[CommitInfo],None,None]:
        follow_files=False
        arglist=[]
        cr=self._load_commits_commit_range(start_commit,end_commit,deafult="")
        if cr:
            arglist.append(cr)
        arglist.append(self.COMMIT_PRETTY_FORMAT)
        if max_count:
            arglist.append(f"--max-count={max_count}")
        if  no_merges:
            arglist.append("--no-merges")
        if author:
            arglist.append(f"--author={author}")
        arglist.extend(self._load_commits_date_range(start_date,end_date))
        if relative_path:
            p=Path(relative_path).as_posix() if isinstance(relative_path,str) else relative_path.as_posix()
            arglist.extend(["--follow",p])
            follow_files=True
        elif filepath:
            p=Path(filepath).relative_to(self.repo_path).as_posix() if isinstance(filepath,str) else filepath.relative_to(self.repo_path).as_posix()
            arglist.extend(["--follow",p])
            follow_files=True
        logger.debug("Loading logs with args",extra={"git_args":arglist})
        return self._log(arglist,follow_files)
    def get_branches(self,deep:bool=True)->Generator[Branch,None,None]:
            if deep:
                    for head in self.repo.branches:
                        b = self.get_branch(head.name)
                        yield b
            else:
                    for head in self.repo.branches:
                        yield Branch(name=head.name,commits=[])
    def get_branch(self,branch:str,diff_branch:Optional[str]=None)->Branch:
        try:
            commits=self._rev_list(only_branch=True,to_commit=branch,from_commit=diff_branch)
        except exc.GitCommandError():
            logger.error("Branch not found")
            raise ValueError("Branch not found")
        return Branch(commits=commits,name=branch)
    
    def count_commits(self,from_commit:Optional[str]=None,to_commit:Optional[str]=None):
        count=0
        try:
            count=int( self._rev_list(only_branch=to_commit !=None,count_only=True,to_commit=to_commit,from_commit=from_commit)[0] )
            
        except exc.GitCommandError():
            logger.error("Branch not found")
            raise ValueError("Branch not found")
        return count
    def get_authors(self)->set[Author]:
        pattern=re.compile(r'([\w\s]+) <([a-z0-9A-Z!#$%@.&*+\/=?^_{|}~-]+)> \(\d+\)')
        authors:set[Author]=set()
        with self.repo_lock:
            per_author:list[str]=self.git_repo.shortlog("-e","--format=%H","HEAD").strip('\n').split('\n\n')
        for a_str in per_author:
            line_list=a_str.split('\n')
            l=line_list.pop(0).strip()
            logger.debug(l)
            name,email=re.match(pattern=pattern,string=l).groups()
            auth=Author(email,name)
            for line in line_list:
                auth.commits_authored.append(line.strip())
            authors.add(auth)
        return authors

    def get_authors_in_range(self,start_date:Optional[date]=None,end_date:Optional[date]=None)->set[Author]:
        pattern=re.compile(r'([\w\s]+) <([a-z0-9A-Z!#$%@.&*+\/=?^_{|}~-]+)> \(\d+\)')
        authors:set[Author]=set()
        arglist=self._load_commits_date_range(start_date,end_date)
        with self.repo_lock:
            per_author:list[str]=self.git_repo.shortlog(*arglist,"-e","--format=%H","HEAD").strip('\n').split('\n\n')
        for a_str in per_author:
            line_list=a_str.split('\n')
            l=line_list.pop(0).strip()
            logger.debug(l)
            name,email=re.match(pattern=pattern,string=l).groups()
            auth=Author(email,name)
            for line in line_list:
                auth.commits_authored.append(line.strip())
            authors.add(auth)
        return authors
    
    def get_commit(self,commit_hash:Optional[str]=None,end_date:Optional[date]=None)->CommitInfo:
        if commit_hash and end_date:
            raise ValueError("Only one between commit_hash and end_date can be used")
        gen=self.lazy_load_commits(max_count=1,end_commit=commit_hash,end_date=end_date)
        commit=next(gen)[0]
        gen=None
        return commit

    def get_last_modified(self,commit:str)->Generator[tuple[str,set[str]],None,None]:
        with self.repo_lock:
            git_repo=git.Git(self.repo_path)
            
        for k,v in git_repo.get_commits_last_modified_lines(git_repo.get_commit(commit)).items():
            yield (k,v)
            
    def get_author_commits(self,name:Optional[str]=None,email:Optional[str]=None)->Generator[list[CommitInfo],None,None]:
        if not name and not email or name and email:
            raise ValueError("Only one between name and email are required")
        val=name if name else email
        return self.lazy_load_commits(author=val)
    
    def get_tracked_files(self)->list[str]:
        with self.repo_lock:
            files=re.split(string=self.git_repo.ls_files(),pattern=r'\r\n|\n|\r')
        return files

    def get_source_code(self,file:Union[str,Path],commit:Optional[str]=None)->list[str]:
        '''
        DEPRECATED
        '''
        text=[]
        file_path=file
        if isinstance(file,str):
            file_path=Path(file)
        with self.repo_lock:
            target_commit=self.repo.commit(commit)
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
    
    def get_commit_files(self,commit:Optional[str]=None)->list[str]:
        cm=commit if commit else "HEAD"
        with self.repo_lock:
            return self.git_repo.ls_tree("-r","--name-only",cm).split("\n")
    
    def get_dir_structure(self,commit:Optional[str]=None)->TreeStructure:
        if not commit and self.tree:
            return self.tree
        with self.repo_lock:
            t=self.repo.commit(commit).tree
            tree = TreeStructure(hash=t.hexsha,content=[])
            for o in t.traverse():
                obj=None
                if isinstance(o,Blob):
                    obj=File(name=o.name,size=o.size,hash_string=o.hexsha)
                else:
                    obj=Folder(name=o.name,content=dict(),hash_string=o.hexsha)
                tree.build(path=o.path,new_obj=obj)
        return tree
            
    def get_source(self, id:str)->list[str]:
        try:
            if self.git_repo.cat_file("-t",id) != "blob":
                raise TypeError(f"Hexsha {id} in not a blob")
        except exc.GitCommandError:
            raise FileNotFoundError("Couldn't retrieve the object")
        return re.split(string=self.git_repo.cat_file("-p",id),pattern=r"\r\n|\r|\n")
    
    def get_file_authors(self):
        pass
    
    #TODO restructure truck factor calculation methods --raw, --numstat, --shortstat, --dirstat, --summary, --name-only, --name-status, --check
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
        for result in map(lambda item:(item,commit_list),authors):
            author,doa=self._calculate_DOA(result)
            author_doa[author]=doa
        return (filepath,author_doa)
    
    def infer_programming_language(self,files:Iterable[str],threshold:float=0.35)->list[str]:
        suffix_count:dict[str,int]=dict()
        fs=set(files)
        tot_files=len(fs)
        ret_suffixes=list()
        for file in fs:
            try:
                suffix=file.rsplit(".",maxsplit=1)[1]
                if suffix not in suffix_count:
                    suffix_count[suffix]=0
                suffix_count[suffix]+=1
            except IndexError:
                pass
        for suff,count in suffix_count.items():
            logger.debug(f"Found suffix {suff} {count} times on {tot_files} files")
            if float(count/tot_files) >= threshold:
                ret_suffixes.append("."+suff)
        return ret_suffixes
    #Calculate using AVI algorithm
    def get_truck_factor(self,path_of_interest:Optional[Iterable[Union[str|Path]]]=None,suffixes_of_interest:Optional[Iterable[Union[str]]]=set(),date_range:Optional[tuple[date,date]]=None,doa_threshold:float=0.75,coverage:float=0.5)->tuple[int,dict[Author,list[str]]]:
        start=None
        end=None
        
        if date_range and len(date_range)<=2:
            try:
                start,end=date_range
            except ValueError:
                start=date_range[0]
        cov=coverage if coverage <=1 else 1/coverage
        doa_th=doa_threshold if doa_threshold else 1/doa_threshold
        if path_of_interest: 
            unfiltered_files:set[str]=set()
            for p in path_of_interest:
                n_p=""
                try:
                    n_p=Path(p).relative_to(self.repo_path).as_posix() if isinstance(p,Path) else p
                except ValueError:
                    n_p=p.as_posix() if isinstance(p,Path) else p
                finally:
                    unfiltered_files.add(n_p)
        else: 
            unfiltered_files=set(self.get_tracked_files())
        if isinstance(unfiltered_files,list):
            logger.debug("Unfiltered files found",extra={"files":unfiltered_files})
        author_files_counter:dict[str,list[str]]=dict()
        files_author_count:dict[str,int]=dict()
        file_relative_commit:dict[str,list[CommitInfo]]=dict()
        orphans=0
        tf=0
        tot_files=0
        authors:dict[str,Author]=dict()
        filters=suffixes_of_interest
        if not suffixes_of_interest:   
            filters=self.infer_programming_language(unfiltered_files)
        exts=set(filters)
        for file in filter(lambda file: check_extension(Path(file).suffix,exts)[0],unfiltered_files):
            logger.debug(f"Checking file {file}")
            file_relative_commit[file]=[]
            files_author_count[file]=0
            for cl in self.lazy_load_commits(relative_path=file,start_date=start,end_date=end):
                file_relative_commit[file].extend(cl)
                for c in cl:
                    if c.author_email not in authors:
                        authors[c.author_email]=Author(c.author_email,c.author_name)
                        author_files_counter[c.author_email]=[]
                    authors[c.author_email].commits_authored.append(c.commit_hash)
        tot_files=len(files_author_count.keys())
        for t in map(lambda item:(item,authors.values()),file_relative_commit.items()):
            file,doas=self.calculate_file_DOA(t)
            for author,doa in doas.items():
                max_doa=sorted(doas.values(),reverse=True)[0]
                if float(doa/max_doa)>= doa_th:
                    author_files_counter[author.email].append(file)
                    files_author_count[file]+=1
        author_sorted_list=sorted(((k,v) for k,v in author_files_counter.items()),key=lambda item:len(item[1]),reverse=True)
        logger.debug("Author sorted DOA list",extra=dict(author_list=author_sorted_list))
        i=int(0)
        while orphans <= int(tot_files*cov):
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
    
