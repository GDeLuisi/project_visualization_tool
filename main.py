import src.utility.logs
__version__="0.0.1"
from pathlib import Path
from src.app.cli import main
base_path=Path.cwd()
test_project=base_path.parent.joinpath("emacs-theme-gruvbox")
if __name__ =="__main__":
    main([base_path.as_posix()],env="DEV")