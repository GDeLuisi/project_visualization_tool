from pathlib import Path
from typing import Union,Generator,Iterator,Literal
import re
import os
import logging

logger = logging.getLogger("File Parser")
ACCEPTED_EXTENSIONS=Literal[".js",".py",".sh",".sql",".c",".cpp",".php",".html",".java",".rb"]
def fetch_source_files(project_path:Union[Path|str],extensions:set[str],exclude_dirs:set[str]=[".venv",".git",".pytest_cache"])->Generator[Path,None,None]:
    # info("Entered fetch_source_files function")
    path = project_path
    if isinstance(path,str):
        path = Path(project_path)
    if not path.exists():
        logger.critical("Path does not exist")
        raise FileNotFoundError("Path does not exist")
    # info(f"Path {path.as_posix()} Exists")
    if not path.is_dir():
        logger.critical("Path is not a directory")
        raise NotADirectoryError("Path is not a directory")
    # info(f"Path {path.as_posix()} is a directory")
    for item in path.iterdir():
        if item.is_dir() and item.name in exclude_dirs:
            continue
        elif item.is_dir():
            for i in fetch_source_files(item,extensions):
                yield i
        elif item.suffix in extensions:
            yield item
#TODO could be optimized using multiprocessing
def _comment_finder(text:Union[str,list[str]],single_line_pattern:list[str],multi_line_pattern:list[str])->list[tuple[int,int,str]]:
    content=[]
    txt=""
    multi_line:Iterator[re.Match[str]] = ()
    comments:list[tuple[int,int,str]] = []
    if isinstance(text,str):
        txt=text
        content=text.splitlines()
    else:
        txt="".join(text)
        content=text
    for i, line in enumerate(content, 1):
        for pattern in single_line_pattern:
            single_line = re.findall(pattern, line)
            if single_line:
                comments.append((i,i, single_line[0]))
    for pattern in multi_line_pattern:
        multi_line = re.finditer(pattern, txt)
        for match in multi_line:
            matched_string=match.group()
            start_line = txt[:match.start()].count('\n') + 1
            end_line = matched_string.count('\n') + start_line
            comments.append((start_line,end_line, matched_string))
    return comments

def find_file_comments_with_locations(filename:Union[str,Path])->list[tuple[int,int,str]]:
    """Find all comments inside a file discriminating comments markers from code language inferred from the file extension 

    Args:
        filename (Union[str,Path]): path to the file

    Raises:
        FileNotFoundError: if file is not readable

    Returns:
        list[tuple[int,int,str]]: a list of triplets organized as follows: comment start n° line, comment end n° line, comment string
    """    
    filepath=filename
    if isinstance(filename,Path):
        filepath=filename.as_posix()
    if not os.path.isfile(filepath):
        logger.critical(f"Path {filepath} is not a file or does not exist")
        raise FileNotFoundError(f"Path {filepath} is not a file or does not exist")
    _, ext = os.path.splitext(filepath)
    
    with open(filepath, 'r') as file:
        content = file.readlines()
        
    return find_comments_with_locations(content,ext=ext)

def find_comments_with_locations(text:Union[str|list[str]],ext:ACCEPTED_EXTENSIONS)->list[tuple[int,int,str]]:
    """Find all comments inside a string discriminating comments markers from code language inferred from the file extension 

    Args:
        text (Union[str | list[str]]): text to parse
        ext (ACCEPTED_EXTENSIONS): virtual extension of the text 

    Returns:
        list[tuple[int,int,str]]: a list of triplets organized as follows: comment start n° line, comment end n° line, comment string
    """    
    content=text
    if isinstance(text,str):
        content=re.split(string=text,pattern=r'\r\n|\n|\r')
    comments:list[tuple[int,int,str]] = []
    
    if ext in ['.py', '.rb',".sh"]:
        if ext ==".sh":
            comments =_comment_finder(content,[r'#.*'],[r':\'[\s\S]*?\''])
        else:
            comments =_comment_finder(content,[r'#.*'],[r'"""[\s\S]*?"""'])
            
    elif ext in ['.js', '.java', '.c', '.cpp',".php",".sql"]:
        if ext == ".php":
            comments=_comment_finder(content,[r'//.*',r'#.*'],[r'/\*[\s\S]*?\*/'])
        elif ext == ".sql":
            comments=_comment_finder(content,[r'//.*',r'--.*'],[r'/\*[\s\S]*?\*/'])
        else:
            comments=_comment_finder(content,[r'//.*'],[r'/\*[\s\S]*?\*/'])
        
    elif ext == '.html':
        # HTML comments
        comments=_comment_finder(content,[],[r'<!--[\s\S]*?-->'])
    else:
        logger.debug(f"Path {ext} not expected for comment finding",extra={"extension":ext})
    # Add more language-specific rules as needed
    return comments

# def find_satd(filepath:Union[Path|str],tags:set[str]={"TODO","FIXME","HACK","XXX"})->dict[int,str]:
#     path = filepath
#     if isinstance(path,str):
#         path = Path(filepath)

    