import pandas as pd
from typing import Iterable
from .data_typing import CommitInfo
from src._internal import Author
from time import strftime,gmtime
from datetime import date

def make_commit_dataframe(commit_list:Iterable[CommitInfo])->pd.DataFrame:
    commit_dict=dict(hash=[],message=[],author=[],date=[],author_email=[],author_name=[],abbr_hash=[],files_modified=[],parent=[],refs=[])
    for commit in commit_list:
        commit_dict['hash'].append(commit.commit_hash),
        commit_dict['abbr_hash'].append(commit.abbr_hash)
        commit_dict["message"].append(commit.subject)
        commit_dict['author_name'].append(commit.author_name)
        commit_dict['author_email'].append(commit.author_email)
        commit_dict['date'].append(commit.date),
        commit_dict['files_modified'].append(commit.files),
        commit_dict['parent'].append(commit.parent),
        commit_dict['refs'].append(commit.refs)
    return pd.DataFrame(commit_dict)
    