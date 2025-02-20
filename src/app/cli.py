from argparse import ArgumentParser,FileType
from .app import start_app
from pathlib import Path
from logging import error,info
from typing import Optional,Sequence
from sys import version_info
import subprocess
import logging

def main(args:Optional[Sequence[str]]=None,cicd_test:bool=False):
    
    if version_info.minor<10:
        logging.exception(f"System Python version {version_info.major}.{version_info.minor} < Python3.10.x . It is mandatory to at least use Python versions > 3.10.x for a correct usage of the application")
        exit(5)
    #check if git is installed
    git_version=""
    try:
        git_version=subprocess.check_output(["git","--version"])
    except subprocess.CalledProcessError as p:
        error("git is not installed on this system. Please install it as it is a required dependecy for this application to function")
        exit(3)
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
    git_dir=Path(dir).joinpath(".git")
    #check if dir is a git repository
    if not git_dir.is_dir():
        error(f"Chosen directory is not a git repository")
        exit(2)
    try:
        subprocess.check_call(["git","-C",dir,"log"])
    except subprocess.CalledProcessError:
        error("Git repo is corrupted, check for your git config files")
        exit(3)
    start_app(dir,cicd_test)
    # find_setd()