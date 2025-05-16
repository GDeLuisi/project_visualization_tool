from pytest import mark,raises,fixture
from pathlib import Path
from _internal.file_parser import fetch_source_files,find_comments_with_locations,find_file_comments_with_locations,find_satd,find_satd_file
from typing import Generator
from utility import logs as log
import logging
log.setup_logging()
logger=logging.getLogger("Parser tester")
workingpath=Path.cwd()
testdata_fetchsource_correct=[
    (workingpath,[".py"],9),
    (workingpath.as_posix(),[".py",".toml"],10),
]
# "Path does not exist"
# "Path is not a directory" .....................
testdata_fetchsource_wrong=[
    (workingpath.joinpath("main.py"),[".py"],"Path is not a directory"),
    (workingpath.joinpath("dont_exist"),[".py"],"Path does not exist"),
    (workingpath.joinpath("main.py"),[".y"],"Path is not a directory"),
]
test_no_file_found=[
    (workingpath.as_posix(),[".y"]),
    (workingpath,[".y"])
    ]

@mark.parametrize("path,extensions,expected",testdata_fetchsource_correct)
def test_fetch_source_files(path,extensions,expected):
    f_list=list(fetch_source_files(path,extensions=extensions))
    assert len(f_list) >= expected
    
@mark.parametrize("path,extensions,expected",testdata_fetchsource_wrong)
def test_fetch_source_files_error(path,extensions,expected):
    with raises((FileNotFoundError,NotADirectoryError)):
        list(fetch_source_files(path,extensions=extensions))
    
@mark.parametrize("path,extensions",test_no_file_found)
def test_no_file_found(path,extensions):
    f_list=list(fetch_source_files(path,extensions=extensions))
    assert len(f_list) >= 0

test_path=workingpath.joinpath("tests")
test_path_content=list(test_path.iterdir())
item=test_path_content.pop().as_posix()
test_path_content.append(item)
@mark.parametrize("path",test_path_content)
def test_find_comments_in_file(path):
    try:
        comments=find_file_comments_with_locations(path)
        if isinstance(path,str):
            path = Path(path)
        logger.debug(f"Found {len(comments)} comments for file {path.as_posix()}")
        logger.debug("Look for comments info in .findings field of this json",extra={"findings":[f"Found comments from {loc[0]} to {loc[1]} in {path.as_posix()}. Comment: {loc[2]}" for loc in comments]})
    except FileNotFoundError as e:
        if isinstance(path,str):
            path = Path(path)
        if path.is_file():
            raise e
        assert str(e) == f"Path {path.as_posix()} is not a file or does not exist"
    else:
        if path.suffix==".txt":
            assert len(comments)==0
        else:
            assert True

def test_find_comments():
    content='import pydriller as git\nimport pydriller.metrics.process.contributors_count as contr\nimport pydriller.metrics.process.history_complexity as history\nimport pydriller.metrics.process.commits_count as comcnt\nfrom .typing import Author\nfrom typing import Optional,Generator,Union\nfrom pathlib import Path\nfrom datetime import datetime\nfrom git import Git,Repo,Blob\nfrom io import BytesIO\nimport re\n\n#TODO implemente a threaded version for optimization\nclass RepoMiner():\n    def __init__(self,repo_path:Union[Path,str]):\n        self.repo_path=repo_path\n        if isinstance(repo_path,Path):\n            self.repo_path=repo_path.as_posix()\n\n    def get_commits_hash(self,since:Optional[datetime]=None,to:Optional[datetime]=None)->Generator[str,None,None]:\n        repo=git.Repository(path_to_repo=self.repo_path,since=since,to=to)\n        return (commit.hash for commit in repo.traverse_commits())\n    \n    def get_commits_between(self,from_commit:str,to_commit:str)->Generator[str,None,None]:\n        repo=git.Repository(path_to_repo=self.repo_path,from_commit=from_commit,to_commit=to_commit)\n        return (commit.hash for commit in repo.traverse_commits())\n    \n    def get_all_authors(self)->set[Author]:\n        repo=git.Repository(path_to_repo=self.repo_path)\n        authors:set[Author]=set((Author(commit.author.email,commit.author.name) for  commit in repo.traverse_commits()))\n        return authors\n\n    def get_author_commits(self,author_name:str)->Generator[str,None,None]:\n        repo=git.Repository(path_to_repo=self.repo_path,only_authors=[author_name])\n        return (commit.hash for commit in repo.traverse_commits())\n\n    def get_file_authors(self,file:str)->set[Author]:\n        repo=git.Repository(path_to_repo=self.repo_path,only_no_merge=True,filepath=file)\n        authors:set[Author]=set((Author(commit.author.email,commit.author.name) for  commit in repo.traverse_commits()))\n        return authors\n    \n    def get_commit(self,commit_hash:str)->git.Commit:\n        repo=git.Repository(path_to_repo=self.repo_path,single=commit_hash)\n        return list(repo.traverse_commits())[0]\n\n    def get_last_modified(self,commit:str):\n        git_repo=git.Git(self.repo_path)\n        return git_repo.get_commits_last_modified_lines(git_repo.get_commit(commit))\n    #TODO include option to use multiple filenames\n    def get_source_code(self,file:Union[str,Path],commit:Optional[str]=None)->list[str]:\n        text=[]\n        file_path=file\n        if isinstance(file,str):\n            file_path=Path(file)\n        git_repo=Repo(self.repo_path)\n        target_commit=git_repo.commit(commit)\n        tree=target_commit.tree\n        #FIXME: improve search method for file\n        for t in tree.traverse():\n            if isinstance(t,Blob) and Path(t.abspath).as_posix()==file_path.as_posix():\n                with BytesIO(t.data_stream.read()) as f:\n           text=re.split(string=f.read().decode(),pattern=r\'\\r\\n|\\n|\\r\')\n        return text\n        # file_path=file\n        # if isinstance(file,Path):\n        #     file_path=file.as_posix()\n        # repo=git.Repository(self.repo_path,single=commit,order="reverse")\n        # list(repo.traverse_commits())[0]\n        # target_commit.\n# def get_diff(repository:str,filepath:str)->dict[str,dict[str, list[tuple[int, str]]]]:\n#     repo=git.Repository(path_to_repo=repository,filepath=filepath,only_no_merge=True,skip_whitespaces=True,order="reverse")\n#     relative_filepath=filepath.removeprefix(repository)[1:].replace("/","\\\\")\n#     diffs:dict[str,dict[str, list[tuple[int, str]]]]=dict()\n#     for commit in repo.traverse_commits():\n#         for f in commit.modified_files:\n#             if f.old_path == relative_filepath or f.new_path == relative_filepath:\n#                 relative_filepath=f.new_path\n#                 if f.old_path != None:\n#                     relative_filepath=f.old_path\n#                 diffs[commit.hash]=f.diff_parsed\n#     return diffs'
    comments=find_comments_with_locations(content,".py")
    logger.debug(f"Found {len(comments)} comments")
    logger.debug("Look for comments info in .findings field of this json",extra={"findings":[f"Found comments from {loc[0]} to {loc[1]}. Comment: {loc[2]}" for loc in comments]})
    assert len(comments)!=0

internal_package=Path.cwd().joinpath("src","_internal")
modules=[item for item in internal_package.iterdir() if item.is_file()]

def test_find_satd():
    path=internal_package.joinpath("file_parser.py")
    try:
        with path.open() as f:
            satds=find_satd(f.read(),path.suffix)
        assert 30 in satds
        assert satds[30] == "TODO could be optimized using multiprocessing"
    except FileNotFoundError as e:
        if path.is_file():
            raise e

@mark.parametrize("path",modules)
def test_find_satd_file(path):
    satds = find_satd_file(filepath=path)
    logger.debug(f"Found these SATDS in file {path.as_posix()}",extra={"satd":satds})