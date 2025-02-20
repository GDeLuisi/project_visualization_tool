import pandas as pd
from typing import Iterable
# from inspect import get_annotations
from .data_typing import CommitInfo
from src._internal import Author,Branch
from time import strftime,gmtime
from datetime import date
from functools import cache
from logging import getLogger

logger=getLogger("Data Preprocessing")


def prune_common_commits(branches:Iterable[Branch]):
    pass
    # for i,b in enumerate(branches):
    #     temp=b.commits.copy()
    #     temp.difference_update((b.commits for a,b in enumerate(branches) if i!=b and temp.issubset(b.commits) ))
    #     b.commits=temp
    
def make_commit_dataframe(commit_list:Iterable[CommitInfo])->pd.DataFrame:
    pass
    # commit_dict=dict(commit_hash=[],subject=[],date=[],author_email=[],author_name=[],abbr_hash=[],files=[],parent=[],refs=[],tree=[])
    # for commit in commit_list:
    #     commit_dict['commit_hash'].append(commit.commit_hash),
    #     commit_dict['abbr_hash'].append(commit.abbr_hash)
    #     commit_dict["subject"].append(commit.subject)
    #     commit_dict['author_name'].append(commit.author_name)
    #     commit_dict['author_email'].append(commit.author_email)
    #     commit_dict['date'].append(commit.date),
    #     commit_dict['files'].append(commit.files),
    #     commit_dict['parent'].append(commit.parent),
    #     commit_dict['refs'].append(commit.refs)
    #     commit_dict["tree"].append(commit.tree)
    # logger.debug(f"Dict to transform {commit_dict}")
    # df= pd.DataFrame(commit_dict)
    # df.set_index("commit_hash",inplace=True,drop=False)
    # return df
def make_author_dataframe(author_list:Iterable[Author])->pd.DataFrame:
    pass
    # auth_dict=dict(name=[],email=[],commits_authored=[])
    # for author in author_list:
    #     auth_dict["commits_authored"].append(author.commits_authored)
    #     auth_dict["email"].append(author.email)
    #     auth_dict["name"].append(author.name)
    # logger.debug(f"Dict to transform {auth_dict}")
    # df= pd.DataFrame(auth_dict)
    # df.set_index("email",inplace=True,drop=False)
    # return df