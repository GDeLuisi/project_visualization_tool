from pathlib import Path
from typing import Union,Generator
from logging import info
def fetch_source_files(project_path:Union[Path|str],extensions:set[str],exclude_dirs:set[str]=[".venv",".git",".pytest_cache"])->Generator[Path,None,None]:
    info("Entered fetch_source_files function")
    path = project_path
    if isinstance(path,str):
        path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError("Path does not exist")
    info(f"Path {path.as_posix()} Exists")
    if not path.is_dir():
        raise NotADirectoryError("Path is not a directory")
    info(f"Path {path.as_posix()} is a directory")
    for item in path.iterdir():
        if item.is_dir() and item.name in exclude_dirs:
            continue
        elif item.is_dir():
            for i in fetch_source_files(item,extensions):
                yield i
        elif item.suffix in extensions:
            yield item
def find_setd():
    pass

def find_custom_setd():
    pass