import src.utility.logs
__version__="0.0.1"
from pathlib import Path
from src.app.cli import main
base_path=Path.cwd()
test_project=base_path.parent.joinpath("pandas")
if __name__ =="__main__":
    main([test_project.as_posix()],env="PROD")