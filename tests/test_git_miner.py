from _internal import git_mining as gm
from pathlib import Path
import utility.logs as log
import logging
from git.exc import GitCommandError,BadName
from pytest import fixture,mark,raises
from pydriller import Git
from _internal.data_typing import Author
from datetime import date
from typing import Sequence
log.setup_logging()
logger=logging.getLogger("Miner tester")
@fixture
def repo_miner():
    repository_path=Path.cwd()
    return gm.RepoMiner(repository_path)


def test_get_all_authors(repo_miner):
    new_set=repo_miner.get_authors()
    logger.debug(f"Found authors {new_set}")
    for author in set([Author("deluisigerardo@gmail.com","Gerardo De Luisi"),Author("102797969+GDeLuisi@users.noreply.github.com","GeggeDL"),Author(email='g.deluisi@reply.it', name='Gerardo De Luisi')]):
        found=False
        for ath in new_set:
            if ath == author:
                found=True
                break
        if not found:
            assert False
    assert True

def get_last(ls:list):
    return ls[-1]
rev_test_args=[
    (False,10,False,None,None,None,None,False,len,10),
    (False,10,True,None,None,None,None,False,None,10),
    (False,-1,True,None,None,None,None,False,get_last,"c38d21165cc5db6a345beee77adaa60691de0525"),
    (False,0,True,None,None,None,None,False,None,1),
    (False,100,True,None,None,None,"development",True,None,100),
    (False,10,True,None,None,None,"main",True,None,10),
    (False,100,True,None,None,None,"non_exist",True,None,None),
    (True,10,True,None,None,"development","main",True,any,True),
    
]
@mark.parametrize("no_merges,max_count,count_only,start_date,end_date,start_commit,end_commit,only_branch,fun_exp,expected",rev_test_args)
def test_rev_list(repo_miner,no_merges,max_count,count_only,start_date,end_date,start_commit,end_commit,only_branch,fun_exp,expected):
    if expected:
        if fun_exp:
            fun_exp(repo_miner._rev_list(only_branch=only_branch,max_count=max_count,no_merges=no_merges,count_only=count_only,from_date=start_date,to_date=end_date,from_commit=start_commit,to_commit=end_commit))==expected
        else:
            repo_miner._rev_list(only_branch=only_branch,max_count=max_count,no_merges=no_merges,count_only=count_only,from_date=start_date,to_date=end_date,from_commit=start_commit,to_commit=end_commit)==expected
    else:
        with raises(GitCommandError):
            repo_miner._rev_list(only_branch=only_branch,max_count=max_count,no_merges=no_merges,count_only=count_only,from_date=start_date,to_date=end_date,from_commit=start_commit,to_commit=end_commit)

def test_get_branches(repo_miner):

    assert set((b.name for b in repo_miner.get_branches()))=={h.name for h in repo_miner.repo.branches}
    assert set((b.name for b in repo_miner.get_branches(False)))=={h.name for h in repo_miner.repo.branches}

def test_get_author(repo_miner):
    assert len(repo_miner.get_author("Gerardo De Luisi"))==2
    with raises(ValueError):
        repo_miner.get_author("Claudia Setaro")

def test_calculate_doa(repo_miner):
    doas=repo_miner.calculate_DOA("main.py")
    assert len(doas.keys())==len(repo_miner.get_authors())
    assert max(doas.values()) == 1
    with raises(ValueError):
        repo_miner.calculate_DOA("man.py")

def test_calculate_dl(repo_miner):
    author = repo_miner.get_author("GeggeDL").pop()
    dl=repo_miner.calculate_DL(author,"main.py")
    assert dl>=0
    with raises(ValueError):
        repo_miner.calculate_DL(author,"man.py")
        
def test_get_author_in_range(repo_miner):
    auth=repo_miner.get_authors_in_range(start_date=date.fromisoformat("2025-02-10"),end_date=date.fromisoformat("2025-02-12"))
    logger.debug(f"Found authors {auth}")
    assert 1==len(auth)
    assert auth.pop().email =="deluisigerardo@gmail.com"

@mark.parametrize("commit_date,expected",argvalues=[(("c38d21165cc5db6a345beee77adaa60691de0525",None),"102797969+GDeLuisi@users.noreply.github.com"),(("c38d21165cc5db6a345beee77adaa60691de0525",date.fromisoformat("2025-02-10")),None),((None,date.fromisoformat("2025-02-10")),"deluisigerardo@gmail.com")])
def test_get_commit(repo_miner,commit_date,expected):
    if expected:
        assert  expected== repo_miner.get_commit(*commit_date).author_email
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
        if not commit:
            assert set(repo_miner.get_commit_files(commit)).issubset(set(repo_miner.get_tracked_files()))
        else:
            assert repo_miner.get_commit_files(commit)==expected
    else:
        with raises(Exception) as e:
            logger.critical(e.exconly())
            repo_miner.get_commit_files(commit)

def test_get_tracked_files(repo_miner):
    files=set()
    for branch in repo_miner.get_branches(False):
        files.update(repo_miner.get_commit_files(branch.name))
    assert files==set(repo_miner.get_tracked_files())
    
def test_get_tracked_dirs(repo_miner):
    tracked=set(repo_miner.get_tracked_dirs())
    dirs=set()
    actual_dirs=[d for d in map(lambda a: Path(a).parents,repo_miner.get_tracked_files())]
    for d in actual_dirs:
        dirs.update(d)
    dirs={d.as_posix() for d in dirs}
    logger.debug("Found tracked dirs",extra={"tracked":tracked,"actual":dirs})
    assert tracked.issubset(dirs)
    
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
#date.fromisoformat("2025-02-10") date.fromisoformat("2025-02-12")
#TODO make it more comprehensive of equivalence classes on extreme values
commits_args=[
    (True,None,None,None,None,None,None,None,None,"success"),
    (True,None,None,None,None,None,None,None,None,"success"),
    (False,None,None,None,None,None,None,None,None,"success"),
    (True,10,None,None,None,None,None,None,None,"success"),
    (False,10,None,None,None,None,None,None,None,"success"),
    (False,None,Path.cwd().joinpath(*'src/app/app.py'.split('/')),None,None,None,None,None,None,"success"),
    (True,None,None,"src/app/cli.py",None,None,None,None,None,"success"),
    (False,None,'project_visualization_tool/src/app/app.py',"src/app/cli.py",None,None,None,None,None,"success"),
    (True,None,None,"src/app/cli.py",None,None,None,None,None,"success"),
    (False,None,None,None,date.fromisoformat("2025-02-12"),None,None,None,None,"success"),
    (False,None,None,"src/app/cli.py",None,date.fromisoformat("2025-02-12"),None,None,None,"success"),
    (False,None,None,"src/app/cli.py",date.fromisoformat("2025-02-10"),date.fromisoformat("2025-02-12"),None,None,None,"success"),
    (False,None,None,"src/app/cli.py",date.fromisoformat("2025-02-12"),date.fromisoformat("2025-02-10"),None,None,None,"error"),
    (False,None,None,"src/app/cli.py",None,None,"4ba76502c258bf81ebb8cd5db3860eda165536a4","fc476fd9aaced5e81de149e050a79cd8cc544cdd",None,"success"),
    (False,None,None,"src/app/cli.py",None,None,"4ba76502c258bf81ebb8cd5db3860eda165536a4","fc476fd9aaced5e81de149e050a79cd8cc544cdd","deluisigerardo@gmail.com","success"),
    (False,None,None,None,date.fromisoformat("2025-02-10"),date.fromisoformat("2025-02-12"),"4ba76502c258bf81ebb8cd5db3860eda165536a4","fc476fd9aaced5e81de149e050a79cd8cc544cdd",None,"success")
]
@mark.parametrize("no_merges,max_count,filepath,relative_path,start_date,end_date,start_commit,end_commit,author,expected",commits_args)
def test_get_lazy_commits(repo_miner,no_merges,max_count,filepath,relative_path,start_date,end_date,start_commit,end_commit,author,expected):
    # logger.debug(list(Git(Path.cwd()).get_list_commits()))
    if expected=="success":
        commits=[]
        for commit_list in repo_miner.lazy_load_commits(no_merges,max_count,filepath,relative_path,start_date,end_date,start_commit,end_commit,author):
            # logger.debug("Lazy load",extra={"commits":commit_list})
            commits.extend(commit_list)
        logger.debug("Full extracted commits",extra={"commits":commits})
        logger.debug("Len extracted commits ",extra={"len":len(commits)})
        assert True
    else:
        with raises((Exception,ValueError)):
            repo_miner.lazy_load_commits(no_merges,max_count,filepath,relative_path,start_date,end_date,start_commit,end_commit,author)

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
    
truck_factor_testcases=[((".py",".json"),0.75,0.5,1),
                        ((),0.75,0.5,1),
                        (None,-0.75,0.5,None),
                        (None,0.75,-0.5,None),]
                        

@mark.parametrize("suffixes,th,cov,expected",truck_factor_testcases)
def test_calculate_truck_factor(repo_miner,suffixes,th,cov,expected):
    if expected!=None:
        tf=repo_miner.get_truck_factor(suffixes,th,cov)[0]
        assert tf==1
    else:
        with raises(ValueError):
            repo_miner.get_truck_factor(suffixes,th,cov)

    
    
def test_get_count(repo_miner):
    assert repo_miner.count_commits() >0
    assert repo_miner.count_commits("development")>=0
    assert repo_miner.count_commits(to_commit="development")>0
    assert repo_miner.count_commits("development","main")>=0

def test_get_dir_structure(repo_miner):
    tree = repo_miner.get_dir_structure()
    assert next(tree.find("dir_info.py","file")).name == "dir_info.py" 
    repo_miner.get_dir_structure("development")
    repo_miner.get_dir_structure("main")
    repo_miner.get_dir_structure("dir_structure")
    with raises(BadName):
        repo_miner.get_dir_structure("asdjhgasdhgajsdhg")
