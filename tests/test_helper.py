from pytest import mark,fixture,raises
from dataclasses import dataclass,field
from src.utility.helper import *
from src.utility.filters import filter,Filter,FilterFactory,sorter_provider,sorter
from src.app.helper import *
from src._internal.file_parser import DEFAULT_SATD_HIGHLIHGTER
from repository_miner import RepoMiner
from pathlib import Path
main_path=Path.cwd()
test_project=main_path.parent.joinpath("pandas")
@fixture
def git():
    return RepoMiner(main_path.as_posix())

@dataclass
class SerializableTestDataClass():
    a:str
    b:int
    d:dict
    c:list = field(default_factory=lambda: [])
    
    
class SerializableTestClass():
    
    def __init__(self,
                a:str
                ,b:int
                ,c:list
                ,d:dict):
        self.a=a
        self.b=b
        self.c=c
        self.d=d
    

@mark.parametrize("files",[("src/app.py","tests/report.txt","tests/test_dummy.py","tests/test_file_parser.py"),(".github/workflows/test-dev.yml",".github/workflows/testpypi_publish.yml",".gitignore","LICENSE","RAD.docx","README.md","main.py","pyproject.toml","requirements.txt","src/_internal/__init__.py","src/_internal/data_preprocessing.py","src/_internal/data_typing.py","src/_internal/file_parser.py","src/_internal/git_mining.py","src/_internal/info/ext.json","src/app/__init__.py","src/app/app.py","src/app/cli.py","src/gui/__init__.py","src/gui/components.py","src/gui/pages/homepage.py","src/utility/__init__.py","src/utility/logging_configs/logs_config_file.json","src/utility/logging_configs/logs_config_file_old.json","src/utility/logs.py","tests/test_cli.py","tests/test_data_preprocessing.py","tests/test_dummy.py","tests/test_file_parser.py","tests/test_git_miner.py")])
def test_infer_programming_language(files):
    assert infer_programming_language(files)==[".py"]

@mark.parametrize("numbers,comparison,expected",[
    ([1,5,2,6,3,8,34,6,3,7,3,789,3,5,3,55],33,3),
    ([1,5,2,6,3,8,34,6,3,7,3,789,3,5,3],33,2),
    ([1,5,2,6,3,8,6,3,7,3,3,5,3],33,0),
])
def test_filter_functions(numbers,comparison,expected):
    @filter("test_func")
    def test(value,comparison):
        return value > comparison
    fil:Filter = FilterFactory.create_filter("test_func")
    filtered=list(fil.run(numbers,comparison))
    assert len(filtered)==expected
    
@mark.parametrize("commit_sha,path_filter,expected",[
    ("HEAD",{"tests/test_cli.py"},True),
    ("",{"tests/test_cli.py"},False),
    (None,{"tests/test_cli.py"},False),
    ("HEAD",{},True),
])
def test_build_tree(git,commit_sha,path_filter,expected):
    if expected:
        build_tree_structure(git,commit_sha,path_filter)
    else:
        with raises(Exception):
            build_tree_structure(git,commit_sha,path_filter)

def test_retrieve_satds(git):
    files=[]
    for hg in DEFAULT_SATD_HIGHLIHGTER:
        files.extend(git.git.grep(["-l","-E",f'\"[^a-zA-Z0-9_]+\\s*({hg}).+\"']).split("\n"))
    satds=retrieve_SATDs(git,DEFAULT_SATD_HIGHLIHGTER)
    assert set(files) == set(satds.keys())

def test_retreive_contribution():
    df,tf=retrieve_contribution_data(main_path)
    print(tf)

def test_parallel_commit_retrieval(git):
    cl=git.retrieve_commit_list(merges=True)
    assert sorted(cl,key=lambda c: c.abbr_hash) ==sorted(parallel_commit_retrievial(git),key=lambda c: c.abbr_hash)
    
def test_dataframe_serialization():
    o1=SerializableTestDataClass("ciao",1,{"b":["a"]},["giovanni"])
    o2=SerializableTestClass("abc",2,["tommaso"],{})
    d1=get_dataframe(o1)
    d2=get_dataframe(o2)
    data1=dict(
        a=["ciao"],
        b=[1],
        d=[{"b":["a"]}],
        c=[["giovanni"]]
    )
    data2=dict(
        a=["abc"],
        b=[2],
        c=[["tommaso"]],
        d=[{}]
    )
    df1=pd.DataFrame(data1)
    df2=pd.DataFrame(data2)
    pd.testing.assert_frame_equal(df1,d1)
    pd.testing.assert_frame_equal(df2,d2)
