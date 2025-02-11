from _internal import git_mining as gm
from pathlib import Path
import utility.logs as log
import logging
from pytest import fixture,mark
from pydriller import Git
from _internal.data_typing import Author
log.setup_logging()
logger=logging.getLogger("Miner tester")
@fixture
def repo_miner():
    repository_path=Path.cwd()
    return gm.RepoMiner(repository_path)


def test_get_all_authors(repo_miner):
    new_set=repo_miner.authors
    logger.debug(new_set)
    for author in set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL"),Author(email='g.deluisi@reply.it', name='Gerardo De Luisi')]):
        found=False
        for ath in new_set:
            if ath == author:
                found=True
                break
        if not found:
            assert False
    assert True
        
def test_get_commit_author(repo_miner):
    try:
        commit=repo_miner.get_commit("f188112d478439ab9b6d5dad88cf14c46a0efa44")
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    name=commit.author_name
    assert name=="Gerardo De Luisi"

def test_get_author_commits(repo_miner):
    sumlist=0
    for author in repo_miner.authors:
        sumlist+=len(repo_miner.get_author_commits(author.name,author.email))
    totlist=len(repo_miner.commits_info.keys())
    logger.debug(f"Totlist: {totlist}\nSum: {sumlist}")
    assert totlist == sumlist

def test_track_bug():
    pass

def test_get_diff(repo_miner):
    # diff = repo_miner.get_diff(repository_path,Path(repository_path).joinpath("main.py").as_posix())
    # info(diff)
    # assert diff != {}
    pass

def test_get_file_authors(repo_miner):
    main_set=set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL")])
    ret_set=set(repo_miner.get_file_authors(Path.cwd().joinpath(".github","workflows","test-dev.yml")))
    logger.debug(f"Returned set={ret_set}")
    for auth in ret_set:
        if auth not in main_set:
            assert False
    assert True

def test_get_bug_introducing_commit():
    pass

def test_get_bug_resolving_commit():
    pass

def test_get_all_commits(repo_miner):
    # logger.debug(list(Git(Path.cwd()).get_list_commits()))
    commits=[]
    for commit_list in repo_miner.lazy_load_commits():
        logger.debug("Lazy load",extra={"commits":commit_list})
        commits.extend(commit_list)
    logger.debug("Full extracted commits",extra={"commits":commits})
    logger.debug("Len extracted commits ",extra={"len":len(commits)})
    assert True

def test_get_last_modified(repo_miner):
    try:
        commits=repo_miner.get_last_modified("f188112d478439ab9b6d5dad88cf14c46a0efa44")
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    logger.debug(commits)
    assert commits!=set()

@mark.parametrize("commit",["13beba471c644abfc15c07d4559b77a4e7faa787",None])
def test_get_source_code(repo_miner,commit):
    text=repo_miner.get_source_code(Path.cwd().joinpath("tests","test_dummy.py"),commit)
    assert text == ['#TODO dummy test', 'def test_dummy():', '    pass', '', '"""', 'TODO multiple line test', '"""', '']

def test_calculate_truck_factor(repo_miner):
    tf=repo_miner.get_truck_factor()
    logger.debug(list(map(lambda k: (k[0],len(k[1])),tf[1].items())))
    assert tf[0]==1