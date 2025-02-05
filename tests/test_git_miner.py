from _internal import git_mining as gm
from pathlib import Path
import utility.logs as log
import logging
from pytest import fixture
from pydriller import Git
from _internal.typing import Author
log.setup_logging()
logger=logging.getLogger("Miner tester")
@fixture
def repo_miner():
    repository_path=Path.cwd()
    return gm.RepoMiner(repository_path)


def test_get_all_authors(repo_miner):
    new_set=repo_miner.get_all_authors()
    logger.debug(new_set)
    assert len(new_set.difference(set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL")]))) == 0

def test_get_commit_author(repo_miner):
    try:
        commit=repo_miner.get_commit("f188112d478439ab9b6d5dad88cf14c46a0efa44")
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    name=commit.author.name
    assert name=="Gerardo De Luisi"

def test_get_author_commits(repo_miner):
    gdlist=list(repo_miner.get_author_commits("GeggeDL"))
    delist=list(repo_miner.get_author_commits("Gerardo De Luisi"))
    totlist=list(repo_miner.get_commits_hash())
    logger.debug(f"Totlist: {len(totlist)}\nSum: {len(gdlist)+len(delist)}")
    assert len(totlist) == (len(gdlist)+len(delist))

def test_get_commit_between(repo_miner):
    assert len(list(repo_miner.get_commits_between("4a6869eaa1bc585c5552d69c0c841e19a3bb642d","f188112d478439ab9b6d5dad88cf14c46a0efa44")))>0
    
def test_get_truck_factor():
    pass

def test_track_bug():
    pass

def test_get_diff(repo_miner):
    # diff = repo_miner.get_diff(repository_path,Path(repository_path).joinpath("main.py").as_posix())
    # info(diff)
    # assert diff != {}
    pass

def test_get_file_authors(repo_miner):
    assert repo_miner.get_file_authors(Path.cwd().joinpath(".github","workflows","test-dev.yml")) == set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL")])

def test_get_bug_introducing_commit():
    pass

def test_get_bug_resolving_commit():
    pass

def test_get_all_commits(repo_miner):
    logger.debug(list(Git(Path.cwd()).get_list_commits()))
    assert len(list(repo_miner.get_commits_hash())) == len(list((commit.hash for commit in Git(Path.cwd()).get_list_commits())))

def test_get_last_modified(repo_miner):
    try:
        commits=repo_miner.get_last_modified("f188112d478439ab9b6d5dad88cf14c46a0efa44")
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    logger.debug(commits)
    assert commits!=set()