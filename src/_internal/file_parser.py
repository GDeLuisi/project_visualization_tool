from pathlib import Path
from typing import Union,Generator
def fetch_source_files(project_path:Union[Path|str],extensions:list[str])->Generator[Path,None,None]:
    path = project_path
    if isinstance(path,str):
        path = Path(project_path)
        assert path.exists(), "Path does not exist"
    assert path.is_dir() , "Path is not a directory"
    for item in path.iterdir():
        if item.is_dir():
            fetch_source_files(item,extensions)
        elif item.suffix in extensions:
            yield item
def find_setd():
    pass

def find_custom_setd():
    pass