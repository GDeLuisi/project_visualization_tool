from pathlib import Path
from typing import Union,Generator,Iterator,Literal
import re
import os
import logging
from .data_typing import ACCEPTED_EXTENSIONS
logger = logging.getLogger("File Parser")
DEFAULT_SATD_HIGHLIHGTER={"TODO","FIXME","HACK","XXX"}
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
# TODO could be optimized using multiprocessing
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
    
    with open(filepath, 'r',encoding="utf-8") as file:
        content = file.readlines()
        
    return find_comments_with_locations(content,ext=ext)

def find_comments_with_locations(text:Union[str|list[str]],ext:str)->list[tuple[int,int,str]]:
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

def _find_satd_inline(text:str,tags):
    for tag in tags:
        mt:re.Match = re.match(f"^\\W+\\s*({tag}.*)",text)
        if mt and isinstance(mt,re.Match):
            return mt.group(1)
def _find_satd(comments:list[tuple[int,int,str]],tags:list[str])->dict[int,str]:
    satds:dict[int,str]=dict()
    for start,end,comment in comments:
        if start == end:
            txt=_find_satd_inline(comment,tags)
            if txt:
                satds[start]=txt
        else:
            content=re.split(string=comment,pattern=r'\r\n|\n|\r')
            for i,cont in enumerate(content,1):
                txt=_find_satd_inline(cont,tags)
                if txt:
                    satds[start+i]=txt
    return satds
def find_satd_file(filepath:Union[Path|str],tags:set[str]=DEFAULT_SATD_HIGHLIHGTER)->dict[int,str]:
    """Finds all SATD in a file

    Args:
        filepath (Union[Path | str]): path to the file
        tags (set[str], optional): tags used to mark SATD. Defaults to {"TODO","FIXME","HACK","XXX"}.

    Returns:
        dict[int,str]: dictionary with line as key and SATD content as value
    """    
    comments=find_file_comments_with_locations(filename=filepath)
    logger.debug(f"Found comments in file {filepath.as_posix() if isinstance(filepath,Path) else filepath}",extra={"comments":comments})
    return _find_satd(comments,tags)
def find_satd(text:str,extension:str,tags:set[str]=DEFAULT_SATD_HIGHLIHGTER)->dict[int,str]:
    """Finds all SATD in a text

    Args:
        text str: text to analyze.
        extension (ACCEPTED_EXTENSIONS): extention used to infer the programming language.
        tags (set[str], optional): tags used to mark SATD. Defaults to {"TODO","FIXME","HACK","XXX"}.

    Returns:
        dict[int,str]: dictionary with line as key and SATD content as value
    """    
    comments=find_comments_with_locations(ext=extension,text=text)
    logger.debug("Found comments in text",extra={"comments":comments})
    return _find_satd(comments,tags)