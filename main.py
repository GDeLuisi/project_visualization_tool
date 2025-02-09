import src.utility.logs
__version__="0.0.2"
from pathlib import Path
from src.app import start_app

if __name__ =="__main__":
    start_app(Path.cwd())