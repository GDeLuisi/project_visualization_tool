from pytest import mark,raises
from pathlib import Path
from _internal.file_parser import fetch_source_files
from typing import Generator
workingpath=Path.cwd()
testdata_fetchsource_correct=[
    (workingpath,[".py"],9),
    (workingpath.as_posix(),[".py",".toml"],10),
]
# "Path does not exist"
# "Path is not a directory"
testdata_fetchsource_wrong=[
    (workingpath.joinpath("main.py"),[".py"],"Path is not a directory"),
    (workingpath.joinpath("dont_exist"),[".py"],"Path does not exist"),
    (workingpath.joinpath("main.py"),[".y"],"Path is not a directory"),
]
test_no_file_found=[
    (workingpath.as_posix(),[".y"]),
    (workingpath,[".y"])
    ]

# @mark.parametrize("path,extensions,expected",testdata_fetchsource_correct)
# def test_fetch_source_files(path,extensions,expected):
#     f_list=list(fetch_source_files(path,extensions=extensions))
#     assert len(f_list) == expected
    
# @mark.parametrize("path,extensions,expected",testdata_fetchsource_wrong)
# def test_fetch_source_files_error(path,extensions,expected):
#     with raises((FileNotFoundError,NotADirectoryError)):
#         list(fetch_source_files(path,extensions=extensions))
    
# @mark.parametrize("path,extensions",test_no_file_found)
# def test_no_file_found(path,extensions):
#     f_list=list(fetch_source_files(path,extensions=extensions))
#     assert len(f_list) == 0