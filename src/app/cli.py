from argparse import ArgumentParser,FileType
from .app import start_app
from pathlib import Path
from typing import Optional,Sequence
from sys import version_info
import subprocess
import logging
import os
from src.utility._version import __version__
from src.utility.logs import setup_logging
logger=logging.getLogger("cli")
def main(args:Optional[Sequence[str]]=None,cicd_test:bool=False,env:str="PROD"):
    setup_logging(env=env)
    if version_info.minor<10:
        logger.exception(f"System Python version {version_info.major}.{version_info.minor} < Python3.10.x . It is mandatory to at least use Python versions > 3.10.x for a correct usage of the application")
        exit(5)
    #check if git is installed
    git_version=""
    try:
        git_version=subprocess.check_output(["git","--version"])
    except subprocess.CalledProcessError as p:
        logger.error("git is not installed on this system. Please install it as it is a required dependecy for this application to function")
        exit(3)
    parser=ArgumentParser(prog="project-viewer")
    parser.add_argument('dir',nargs='?', default=Path.cwd().as_posix(), type=str)
    parser.add_argument('-v',"--version",action='store_true')
    parsed_args=parser.parse_args(args)
    if parsed_args.version==True:
        print("project-viewer "+__version__)
        exit(0)
    namespace=parsed_args.dir
    dir=str(namespace)
    if dir==".":
        dir=Path.cwd().as_posix()
    logger.info(f"Opening git repository at {dir}")
    if not Path(dir).is_dir():
        logger.error(f"Path {dir} is not a directory")
        exit(1)
    git_dir=Path(dir).joinpath(".git")
    #check if dir is a git repository
    if not git_dir.is_dir():
        logger.error(f"Chosen directory is not a git repository")
        exit(2)
    try:
        subprocess.check_call(["git","-C",dir,"rev-parse","--git-dir"],stderr=open(os.devnull, 'wb'),stdout=open(os.devnull, 'wb'))
    except subprocess.CalledProcessError:
        logger.error("Git repo is corrupted, check for your git config files")
        exit(3)
    logger.info(f"Starting application")
    start_app(Path(dir).resolve().absolute().as_posix(),cicd_test,env=env)
    # find_setd()