from pytest import mark,raises,fixture
from src._internal.data_typing import Author,File,Folder,TreeStructure
from src._internal.data_preprocessing import getMaxMinMarks,unixTimeMillis,unixToDatetime,getMarks
from datetime import date
from src._internal.exceptions import ObjectNotInTreeError,PathNotAvailableError
import datetime as dt
import pandas as pd
from utility import logs as log
from pathlib import Path
import logging
log.setup_logging()
logger=logging.getLogger("Data preprocessor tester")

@fixture
def tree():
    fo=Folder("folder1",dict(file1=File("file1",10,"asdasdasd"),folder2=Folder("folder2",dict(),"kljfjf")),"kljklfjlfkj")
    fi=File("file2",size=12,hash_string="dsfdgds")
    return TreeStructure("sajdhasjdhk",[fo,fi])

today=int(dt.datetime.today().timestamp())-1000
# pd.to_datetime(,unit='s')
later=(dt.datetime.now().timestamp())
def test_marks():
    assert len(getMarks([pd.to_datetime(today,unit='s'),pd.to_datetime(later,unit='s')],2).keys())==1
    assert len(getMarks([pd.to_datetime(today,unit='s'),pd.to_datetime(later,unit='s')],1).keys())==0
    with raises(ZeroDivisionError):
        len(getMarks([pd.to_datetime(today,unit='s'),pd.to_datetime(later,unit='s')],0).keys())==2
def test_max_min_marks():
    assert len(getMaxMinMarks(pd.to_datetime(today,unit='s'),pd.to_datetime(later,unit='s')).keys())==2

def test_unixtimemillis():
    assert int(unixTimeMillis(pd.to_datetime(today,unit='s'))/10000)==int(today/10000)
    logger.debug(unixTimeMillis(pd.to_datetime(-1,unit='s')))
    
def test_unixToDatetime():
    assert unixToDatetime(unixTimeMillis(pd.to_datetime(today,unit='s')))==pd.to_datetime(today,unit='s',utc=True)
    logger.debug(unixToDatetime(-1))
    
tree_walk_args=[
    ("file2",False,False,[File("file2",size=12,hash_string="dsfdgds")]),
    ("folder1",False,False,[File("file1",10,"asdasdasd"),Folder("folder2",dict(),"kljfjf")]),
    ("folder1",False,True,[Folder("folder2",dict(),"kljfjf")]),
    ("folder1",True,False,[File("file1",10,"asdasdasd")]),
    ("file1",False,False,None),
    ("file1",True,True,None),
    ("file3",False,False,None),
]
@mark.parametrize("name,fo,do,expected",tree_walk_args)
def test_walk_folder(tree,name,fo,do,expected):
    if expected:
        assert set(tree.walk_folder(name,fo,do))==set(expected)
    else:
        with raises((ObjectNotInTreeError,ValueError,TypeError)):
            list(tree.walk_folder(name,fo,do))

tree_walk=[
    (False,False,[File("file1",10,"asdasdasd"),File("file2",size=12,hash_string="dsfdgds"),Folder("folder1",dict(file1=File("file1",10,"asdasdasd"),folder2=Folder("folder2",dict(),"kljfjf")),"kljklfjlfkj"),Folder("folder2",dict(),"kljfjf")]),
    (False,True,[Folder("folder2",dict(),"kljfjf"),Folder("folder1",dict(file1=File("file1",10,"asdasdasd"),folder2=Folder("folder2",dict(),"kljfjf")),"kljklfjlfkj")]),
    (True,False,[File("file2",size=12,hash_string="dsfdgds"),File("file1",10,"asdasdasd")]),
    (True,True,None),
]
@mark.parametrize("fo,do,expected",tree_walk)
def test_walk(tree,fo,do,expected):
    if expected:
        assert set(list([o for p,o in tree.walk(fo,do)]))==set(expected)
    else:
        with raises((ObjectNotInTreeError,ValueError,TypeError)):
            list([o for p,o in tree.walk(fo,do)])
tree_find_args=[
    ("file2","folder",[]),
    ("folder1","folder",[Folder("folder1",dict(file1=File("file1",10,"asdasdasd"),folder2=Folder("folder2",dict(),"kljfjf")),"kljklfjlfkj")]),
    ("file1","file",[File("file1",10,"asdasdasd")]),
    ("file2","file",[File("file2",size=12,hash_string="dsfdgds")]),
    ("file1",None,[File("file1",10,"asdasdasd")]),
    ("file1","d",None),
    ("file1","folder",[]),
    
]
@mark.parametrize("name,tp,expected",tree_find_args)
def test_find(tree,name,tp,expected):
    if expected!=None:
        assert set(tree.find(name,tp))==set(expected)
    else:
        with raises(TypeError):
            list(tree.find(name,tp))

def test_get_path(tree):
    for p,o in tree.walk():
        if o.name=="folder2":
            assert p=="folder1"
            
@mark.parametrize("path,expected",[("folder1/folder2",Folder("folder2",dict(),"kljfjf")),("file2",File("file2",size=12,hash_string="dsfdgds")),("folder1/file2",None),("folder2",None)])
def test_get(tree,path,expected):
    if expected:
        tree.get(path)==expected
    else:
        with raises(ObjectNotInTreeError):
            tree.get(path)

build_args=[
    ("a/b/c",File("c",0,"asd"),True,File("c",0,"asd")),
    ("a/b/c",File("c",0,"asd"),False,None),
    ("a/b/c",Folder("c",dict(),"asd"),True,Folder("c",dict(),"asd")),
    ("a/b/c",Folder("c",dict(),"asd"),False,None),
    ("c",Folder("c",dict(),"asd"),False,Folder("c",dict(),"asd")),
    ("c",Folder("c",dict(c=File("c",0,"asd")),"asd"),False,Folder("c",dict(c=File("c",0,"asd")),"asd")),
    ("",Folder("c",dict(),"asd"),False,None),
    ("a/b/c",Author("c","d",["asd"]),False,None),
    ("a/b/c",None,False,None),
]
@mark.parametrize("path,obj,mkdir,expected",build_args)
def test_build_tree(path,obj,mkdir,expected):
    if expected:
        tree=TreeStructure(hash="asjd")
        tree.build(path,obj,mkdir)
        assert next(tree.find(expected.name))==expected
    else:
        with raises((ValueError,ObjectNotInTreeError,TypeError)):
            tree=TreeStructure(hash="asjd")
            tree.build(path,obj,mkdir)
            
static_build_args=[
    ("hash","a/b/c",File("c",0,"asd"),True,File("c",0,"asd")),
    ("hash","a/b/c",File("c",0,"asd"),False,None),
    ("hash","a/b/c",Folder("c",dict(),"asd"),True,Folder("c",dict(),"asd")),
    ("hash","a/b/c",Folder("c",dict(),"asd"),False,None),
    ("hash","c",Folder("c",dict(),"asd"),False,Folder("c",dict(),"asd")),
    ("hash","c",Folder("c",dict(c=File("c",0,"asd")),"asd"),False,Folder("c",dict(c=File("c",0,"asd")),"asd")),
    ("hash","",Folder("c",dict(),"asd"),False,None),
    ("hash","a/b/c",Author("c","d",["asd"]),False,None),
    ("hash","a/b/c",None,False,None),
]
@mark.parametrize("hash,path,obj,mkdir,expected",static_build_args)
def test_static_build_tree(hash,path,obj,mkdir,expected):
    if expected:
        tree=TreeStructure.build_tree(hash,path,obj,mkdir)
        assert next(tree.find(expected.name))==expected
    else:
        with raises((ValueError,ObjectNotInTreeError,TypeError)):
            tree=TreeStructure.build_tree(hash,path,obj,mkdir)
            
def test_insertion_build():
    tree =TreeStructure(hash="asjd",content=[Folder("c",dict(d=File("d",0,"aswd"),a=Folder("a",dict(),"sdhf")),"asd")])
    with raises(PathNotAvailableError):
        tree.build("c/d",File("d",0,"sdf"))
    with raises(PathNotAvailableError): 
        tree.build("c/a",Folder("a",0,"sdf"))
