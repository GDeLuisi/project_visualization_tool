from argparse import ArgumentParser,FileType
from .app import open_browser
from src._internal.file_parser import find_setd
from git import Repo,InvalidGitRepositoryError
from pathlib import Path
from logging import error,info
from typing import Optional,Sequence

def main(args:Optional[Sequence[str]]=None):
    parser=ArgumentParser(prog="project-viewer")
    parser.add_argument('dir',nargs='?', default=Path.cwd().as_posix(), type=str)
    namespace=parser.parse_args(args)
    dir=str(namespace.dir)
    if dir==".":
        dir=Path.cwd().as_posix()
    info(f"Opening git repository at {dir}")
    if not Path(dir).is_dir():
        error(f"Path {dir} is not a directory")
        exit(1)
    try:
        repository=Repo(dir)
    except InvalidGitRepositoryError:
        error(f"Chosen directory is not a git directory or it cannot be accessed, please check the directory {dir}")
        exit(2)
    # find_setd()