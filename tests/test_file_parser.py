from pytest import mark,raises
from pathlib import Path
from _internal.file_parser import fetch_source_files,find_comments_with_locations
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
#TODO test todo
"""
@mark.parametrize("path,extensions,expected",testdata_fetchsource_correct)
def test_fetch_source_files(path,extensions,expected):
    f_list=list(fetch_source_files(path,extensions=extensions))
    assert len(f_list) == expected
    
@mark.parametrize("path,extensions,expected",testdata_fetchsource_wrong)
def test_fetch_source_files_error(path,extensions,expected):
    with raises((FileNotFoundError,NotADirectoryError)):
        list(fetch_source_files(path,extensions=extensions))
    
@mark.parametrize("path,extensions",test_no_file_found)
def test_no_file_found(path,extensions):
    f_list=list(fetch_source_files(path,extensions=extensions))
    assert len(f_list) == 0
"""
test_path=workingpath.joinpath("tests")
test_path_content=list(test_path.iterdir())
@mark.parametrize("path",test_path_content)
def test_find_comments(path):
    try:
        comments=find_comments_with_locations(path)
        logger.debug(f"Found {len(comments)} comments for file {path.as_posix()}")
        logger.debug("Look for comments info in .findings field of this json",extra={"findings":[f"Found comments from {loc[0]} to {loc[1]} in {path.as_posix()}. Comment: {loc[2]}" for loc in comments]})
    except FileNotFoundError as e:
        if path.is_file():
            raise e
        assert str(e) == f"Path {path.as_posix()} is not a file or does not exist"
    else:
        if path.suffix==".txt":
            assert len(comments)==0
        else:
            assert len(comments)!=0