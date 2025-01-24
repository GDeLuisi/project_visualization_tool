from pytest import fixture,mark,raises
from pathlib import Path
from src._internal.file_parser import fetch_source_files
from typing import Generator
workingpath=Path.cwd()
testdata_fetchsource_correct=[
    (workingpath,[".py"],6),
    (workingpath.as_posix(),[".py",".toml"],7),
]
# "Path does not exist"
# "Path is not a directory"
testdata_fetchsource_wrong=[
    (workingpath.as_posix(),[".y"],""),
    (workingpath.joinpath("main.py"),[".py"],"Path is not a directory"),
    (workingpath.joinpath("dont_exist"),[".py"],"Path does not exist"),
    (workingpath.joinpath("main.py"),[".y"],"Path is not a directory"),
    (workingpath,[".y"],"")
]

@mark.parametrize("path,extensions,expected",testdata_fetchsource_correct)
def test_fetch_source_files(path,extensions,expected):
    f_list=list(fetch_source_files(path,extensions=extensions))
    assert len(f_list) == expected
    
@mark.parametrize("path,extensions,expected",testdata_fetchsource_wrong)
def test_fetch_source_files_error(path,extensions,expected):
    with raises(AssertionError) as e:
        f_list=(fetch_source_files(path,extensions=extensions))
        assert f_list !=0, ""
    assert str(e.value) == expected