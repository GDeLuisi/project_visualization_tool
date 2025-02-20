from app.cli import main
from pytest import raises,fixture
from sys import argv
from pathlib import Path
workingpath=Path.cwd()
#single line
def test_cli_function():
    argv.clear()
    main(cicd_test=True)

def test_cli():
    main([workingpath.as_posix()],cicd_test=True)

def test_cli_no_dir():
    with raises(SystemExit) as e:
        main([f"{workingpath.joinpath('main.py').as_posix()}"],cicd_test=True)
    assert e.value.code == 1
    
def test_cli_no_git():
    with raises(SystemExit) as e:
        main([f"{workingpath.parent.as_posix()}"],cicd_test=True)
    assert e.value.code ==2