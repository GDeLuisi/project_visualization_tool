import src.utility.logs
__version__="0.0.1"
from pathlib import Path
from src.app.cli import main

if __name__ =="__main__":
    main([Path.cwd().as_posix()])