import src.utility.logs
__version__="0.0.1"
from pathlib import Path
from src.app.cli import main
base_path=Path.cwd()
test_project=base_path.parent.joinpath("pandas")
test_project2=base_path.parent.joinpath("QualiTag")
test_project3=base_path.parent.joinpath("sudoku-gen-n-solve")
test_project4=base_path.parent.joinpath("tensorflow")
if __name__ =="__main__":
    main([base_path.as_posix()],env="PROD")
