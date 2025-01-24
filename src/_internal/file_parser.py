from pathlib import Path
from typing import Union,Generator
def fetch_source_files(project_path:Union[Path|str],extensions:list[str])->Generator[Path,None,None]:
    path = project_path
    if isinstance(path,str):
        path = Path(project_path)
    if not path.exists():
        raise FileNotFoundError("Path does not exist")
    if not path.is_dir():
        raise NotADirectoryError("Path is not a directory")
    for item in path.iterdir():
        if item.is_dir():
            for i in fetch_source_files(item,extensions):
                yield i
        elif item.suffix in extensions:
            yield item
def find_setd():
    pass

def find_custom_setd():
    pass