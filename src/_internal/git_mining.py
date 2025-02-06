import pydriller as git
import pydriller.metrics.process.contributors_count as contr
import pydriller.metrics.process.history_complexity as history
import pydriller.metrics.process.commits_count as comcnt
from .typing import Author
from typing import Optional,Generator,Union
from pathlib import Path
from datetime import datetime
from git import Git,Repo,Blob
from io import BytesIO
import re

#TODO implemente a threaded version for optimization
class RepoMiner():
    def __init__(self,repo_path:Union[Path,str]):
        self.repo_path=repo_path
        if isinstance(repo_path,Path):
            self.repo_path=repo_path.as_posix()

    def get_commits_hash(self,since:Optional[datetime]=None,to:Optional[datetime]=None)->Generator[str,None,None]:
        repo=git.Repository(path_to_repo=self.repo_path,since=since,to=to)
        return (commit.hash for commit in repo.traverse_commits())
    
    def get_commits_between(self,from_commit:str,to_commit:str)->Generator[str,None,None]:
        repo=git.Repository(path_to_repo=self.repo_path,from_commit=from_commit,to_commit=to_commit)
        return (commit.hash for commit in repo.traverse_commits())
    
    def get_all_authors(self)->set[Author]:
        repo=git.Repository(path_to_repo=self.repo_path)
        authors:set[Author]=set((Author(commit.author.email,commit.author.name) for  commit in repo.traverse_commits()))
        return authors

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
        #FIXME: improve search method for file
        for t in tree.traverse():
            if isinstance(t,Blob) and Path(t.abspath).as_posix()==file_path.as_posix():
                with BytesIO(t.data_stream.read()) as f:
                    text=re.split(string=f.read().decode(),pattern=r'\r\n|\n|\r')
        return text
        # file_path=file
        # if isinstance(file,Path):
        #     file_path=file.as_posix()
        # repo=git.Repository(self.repo_path,single=commit,order="reverse")
        # list(repo.traverse_commits())[0]
        # target_commit.
# def get_diff(repository:str,filepath:str)->dict[str,dict[str, list[tuple[int, str]]]]:
#     repo=git.Repository(path_to_repo=repository,filepath=filepath,only_no_merge=True,skip_whitespaces=True,order="reverse")
#     relative_filepath=filepath.removeprefix(repository)[1:].replace("/","\\")
#     diffs:dict[str,dict[str, list[tuple[int, str]]]]=dict()
#     for commit in repo.traverse_commits():
#         for f in commit.modified_files:
#             if f.old_path == relative_filepath or f.new_path == relative_filepath:
#                 relative_filepath=f.new_path
#                 if f.old_path != None:
#                     relative_filepath=f.old_path
#                 diffs[commit.hash]=f.diff_parsed
#     return diffs