from _internal import git_mining as gm
from pathlib import Path
import utility.logs as log
import logging
from pytest import fixture,mark,raises
from pydriller import Git
from _internal.data_typing import Author
from datetime import date
log.setup_logging()
logger=logging.getLogger("Miner tester")
@fixture
def repo_miner():
    repository_path=Path.cwd()
    return gm.RepoMiner(repository_path)


def test_get_all_authors(repo_miner):
    new_set=repo_miner.get_authors()
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
    
def test_get_branches(repo_miner):
    assert set(repo_miner.get_branches())=={"main","development"}

def test_checkout_branch(repo_miner):
    repo_miner.checkout_branch("main")
    repo_miner.checkout_branch("development")

def test_get_author_in_range(repo_miner):
    auth=repo_miner.get_authors_in_range(start_date=date.fromisoformat("2025-02-10"),end_date=date.fromisoformat("2025-02-12"))
    assert 1==len(auth)
    assert auth.pop().email =="deluisigerardo@gmail.com"

@mark.parametrize("commit_date,expected",argvalues=[(("c38d21165cc5db6a345beee77adaa60691de0525",None),"success"),(("c38d21165cc5db6a345beee77adaa60691de0525",date.fromisoformat("2025-02-10")),"error"),((None,date.fromisoformat("2025-02-10")),"success")])
def test_get_commit(repo_miner,commit_date,expected):
    if expected =="success":
        assert "deluisigerardo@gmail.com" == repo_miner.get_commit(*commit_date).author_email
    else:
        with raises(ValueError,match="Only one between commit_hash and end_date can be used"):
            repo_miner.get_commit(*commit_date)
    
def test_get_commit_author(repo_miner):
    try:
        commit=repo_miner.get_commit("f188112d478439ab9b6d5dad88cf14c46a0efa44")
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    name=commit.author_name
    assert name=="Gerardo De Luisi"
    
@mark.parametrize("name_email,expected",[(("GeggeDL","deluisigerardo@gmail.com"),"error"),(("GeggeDL",None),"success"),((None,"deluisigerardo@gmail.com"),"success")])
def test_get_author_commits(repo_miner,name_email,expected):
    if expected =="success":
        assert len(list(repo_miner.get_author_commits(*name_email)))>0
    else:
        with raises(ValueError,match="Only one between name and email are required"):
            repo_miner.get_author_commits(*name_email)
@mark.parametrize("commit,expected",[("f188112d478439ab10b6d5dad88cf14c46a0efa44",[]),(None,[".github/workflows/test-dev.yml",".github/workflows/testpypi_publish.yml",".gitignore","LICENSE","RAD.docx","README.md","main.py","pyproject.toml","requirements.txt","src/_internal/__init__.py","src/_internal/data_preprocessing.py","src/_internal/data_typing.py","src/_internal/file_parser.py","src/_internal/git_mining.py","src/_internal/info/ext.json","src/app/__init__.py","src/app/app.py","src/app/cli.py","src/gui/__init__.py","src/gui/components.py","src/gui/pages/homepage.py","src/utility/__init__.py","src/utility/logging_configs/logs_config_file.json","src/utility/logging_configs/logs_config_file_old.json","src/utility/logs.py","tests/test_cli.py","tests/test_data_preprocessing.py","tests/test_dummy.py","tests/test_file_parser.py","tests/test_git_miner.py"]),("f188112d478439ab9b6d5dad88cf14c46a0efa44",[".github/workflows/python-app-dev.yml",".github/workflows/python-app.yml",".gitignore","LICENSE","README.md","main.py","pyproject.toml","src/_internal/__init__.py","src/_internal/file_parser.py","src/app.py","tests/report.txt","tests/test_dummy.py","tests/test_file_parser.py"])])
def test_get_commit_files(repo_miner,commit,expected):
    if expected:
        assert repo_miner.get_commit_files(commit) == expected
    else:
        with raises(Exception) as e:
            logger.critical(e.exconly())
            repo_miner.get_commit_files(commit)
@mark.parametrize("files",[("src/app.py","tests/report.txt","tests/test_dummy.py","tests/test_file_parser.py"),(".github/workflows/test-dev.yml",".github/workflows/testpypi_publish.yml",".gitignore","LICENSE","RAD.docx","README.md","main.py","pyproject.toml","requirements.txt","src/_internal/__init__.py","src/_internal/data_preprocessing.py","src/_internal/data_typing.py","src/_internal/file_parser.py","src/_internal/git_mining.py","src/_internal/info/ext.json","src/app/__init__.py","src/app/app.py","src/app/cli.py","src/gui/__init__.py","src/gui/components.py","src/gui/pages/homepage.py","src/utility/__init__.py","src/utility/logging_configs/logs_config_file.json","src/utility/logging_configs/logs_config_file_old.json","src/utility/logs.py","tests/test_cli.py","tests/test_data_preprocessing.py","tests/test_dummy.py","tests/test_file_parser.py","tests/test_git_miner.py")])
def test_infer_programming_language(repo_miner,files):
    assert repo_miner.infer_programming_language(files)==[".py"]
    
def test_get_author_commits(repo_miner):
    sumlist=0
    for author in repo_miner.get_authors():
        sumlist+=len(*list(repo_miner.get_author_commits(author.email)))
    totlist=len(*repo_miner.lazy_load_commits())
    logger.debug(f"Totlist: {totlist}\nSum: {sumlist}")
    assert totlist == sumlist

def test_track_bug():
    pass

def test_get_diff(repo_miner):
    # diff = repo_miner.get_diff(repository_path,Path(repository_path).joinpath("main.py").as_posix())
    # info(diff)
    # assert diff != {}
    pass

# def test_get_file_authors(repo_miner):
#     main_set=set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL")])
#     ret_set=set(repo_miner.get_file_authors(Path.cwd().joinpath(".github","workflows","test-dev.yml")))
#     logger.debug(f"Returned set={ret_set}")
#     for auth in ret_set:
#         if auth not in main_set:
#             assert False
#     assert True

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
        commits=dict(repo_miner.get_last_modified("f188112d478439ab9b6d5dad88cf14c46a0efa44"))
    except Exception as e:
        logger.exception(e)
        raise Exception(e)
    logger.debug(commits)
    assert len(commits.values())!=0

@mark.parametrize("commit",["13beba471c644abfc15c07d4559b77a4e7faa787",None])
def test_get_source_code(repo_miner,commit):
    text=repo_miner.get_source_code(Path.cwd().joinpath("tests","test_dummy.py"),commit)
    assert text == ['#TODO dummy test', 'def test_dummy():', '    pass', '', '"""', 'TODO multiple line test', '"""', '']

@mark.parametrize("paths,suffixes,date_range",[(("src/app.py","tests/report.txt","tests/test_dummy.py","tests/test_file_parser.py"),(".py",".json"),(date.fromisoformat("2025-02-01"),date.fromisoformat("2025-02-11"))),((".github/workflows/test-dev.yml",".github/workflows/testpypi_publish.yml",".gitignore","LICENSE","RAD.docx","README.md","main.py","pyproject.toml","requirements.txt","src/_internal/__init__.py","src/_internal/data_preprocessing.py","src/_internal/data_typing.py","src/_internal/file_parser.py","src/_internal/git_mining.py","src/_internal/info/ext.json","src/app/__init__.py","src/app/app.py","src/app/cli.py","src/gui/__init__.py","src/gui/components.py","src/gui/pages/homepage.py","src/utility/__init__.py","src/utility/logging_configs/logs_config_file.json","src/utility/logging_configs/logs_config_file_old.json","src/utility/logs.py","tests/test_cli.py","tests/test_data_preprocessing.py"),(".py",".json"),(date.fromisoformat("2025-02-01"),date.fromisoformat("2025-02-11"))),((),(".py",".json"),(date.fromisoformat("2025-02-01"),date.fromisoformat("2025-02-12"))),((),(),(date.fromisoformat("2025-02-01"),date.fromisoformat("2025-02-12"))),((),(),(date.fromisoformat("2025-02-01"),None)),((),(),(None,date.fromisoformat("2025-02-12"))),((),(),())])
def test_calculate_truck_factor(repo_miner,paths,suffixes,date_range):
    tf=repo_miner.get_truck_factor(paths,suffixes_of_interest=suffixes,date_range=date_range)
    # logger.debug(list(map(lambda k: (k[0],len(k[1])),tf[1].items())))
    assert tf[0]==1