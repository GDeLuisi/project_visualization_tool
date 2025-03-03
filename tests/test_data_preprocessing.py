from pytest import mark,raises,fixture
from src._internal.data_typing import Author,CommitInfo,File,Folder,TreeStructure
from time import strptime,struct_time,mktime,gmtime,time
from src._internal import make_author_dataframe,make_commit_dataframe
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
authors=[Author(email='102797969+GDeLuisi@users.noreply.github.com', name='GeggeDL', commits_authored=['c38d21165cc5db6a345beee77adaa60691de0525', 'b8926be15d53a3a8a77962325df5c3d52a811a8e', 'a46659a44163ddc441a76068dd831ff03233a852', '838001a8f0448c0d1f04c936854da73f7da85150', '0f794611e42d9f432cf7955143f378927eedd032']),
         Author(email='g.deluisi@reply.it', name='Gerardo De Luisi', commits_authored=['78d7a37bad672558cf455e776d9d75e527ddea94']), 
         Author(email='deluisigerardo@gmail.com', name='Gerardo De Luisi', commits_authored=['700308b91a49af60d815f820287f330421036800', '8ff94218d8104d4df9b8760d97b78f23bf4e65f4', '82045a3b987491f5ca58e2f30ae97019c3a21caa', '42474dab198f86788f5299e29cc8d9d782e78b26', '90430e9802a0aec07c6ce555fdce446e8dbbdde4', 'f8bea27f53ebc5b9d6eb2bf403a984759cbdf9bb', 'ed72bdfef32679c530643ac4b88cf84290b4db06', 'd8834bf9f38775274c3dd8c3af2a6c52e579fae6', '1636d9856ef64c180496a51b0314abac9ee2d499', '2395d60a6eadee1c631ef9a6f4b997a65dacdc3b', '37448002161962999c95c8ec99495106c122c9a0', '6eab467c142835a89f7b34df85fc6bf2dd20c8e0', 'e5a57f5ea722e2cafa266401bd40abfa82f7bbf9', '657ea7bb3738d2034a3dcc87dfcc211d7622eb7c', 'b7c960b302cd2029345c11297dc99c64a94433e9', 'f188112d478439ab9b6d5dad88cf14c46a0efa44', 'cdfdfe4093b72736d611f38ea453b56df2bee565', '6ce5e23301295f7488c330217d166b1285b2a413', 'efcde250af885b01f12e01438c2a1c256d4f3c02', '7f927b70563af7a62d36983e5b9e0797aaa81fa9', 'f46a2018e8da45d33cd4ef28278cf66625fc4de3', '548f37d86a86410f19f7c3cc768f7fb4042756a9', '36c1c55545b62379589efd17127463f50e94b01a', '9b9ce7ee55be4e8773a28916798492792d76f696', 'a37ebf1202038e8e90b91cd5ce442ba409f64d19', 'e2cf890f1a17b922e7aab36d5d48b2caa0d75890', '991d64a81dd8f2c1aa9b099b496c2611aa89f7e9', '224cc5e3e292f5517d09cd8a71047340223ea7fe', '9828858542ee3024c237008db3e2c10fc1baae5c', '1e45e3e89c7f211a2baa926c3df22764aadaab2c', '144dbb52ab2671e1229ff5eb0b1ced03c2421e02', '5a5699e34f3b4915d50a0d5dbc8f8d4b698336a3', 'eae1c74f68ebc802a75efa35c99f604ef5644792', 'd9a53ab8fc8b9d8a395a00855ebb7b63ed102b8b', '41140abfd837ff936d7532ddec6d5e07e395f33b', '67cbd113d557b08dde1f337327567bbf50fb9b73', 'b1d38786cbc2c4b562c8df9828ee3f0da4b73374', '59e569fc42682a721a50b0bd267a9134d9999580', '98ba927615cfa8e4ba336f5fc1662414af80145d', '4ba76502c258bf81ebb8cd5db3860eda165536a4', '02644740c673c29c7a8d2fa4f608affeddb5c317', '52e8f399d77df5c68835064ba8c6d771d6c7e71d', '22ebbb23f676499a5e3a67ed4968ff6b12bf52af', 'b9c09cf71e9225e22769d84c623615cdceee50c2', '13beba471c644abfc15c07d4559b77a4e7faa787', '5387d3c1eab23efb1c86864856c39c942d7e9cda', 'fbe9bb37f85a3bec2fe3f4a35a443ad56757ea52', '2f1cd27f6e649c14acbc7cce129938bf41240351', 'bcf2ebaa9fd0b687a884f56149f4e20dde45afdb', '9332f00ccfa3d3a1d1849417ccd50cc88b1703b9', '974489ae941fad4d0fe15a4f939c69aec62df701', '586dd3460b2e881d7ea2af6c9865536ef67afee6', 'bae1282fbd9598138fadebeb7bb16bd35a97080f', 'fd321c1057b16022ba1f54aa3841772e5038b708', '81dfde5cb8d491d081f15c5c454f17ede803771c', '088c743d2d7a7181faa6adeac821f89d63c693ed', '1343fbe64f7b48621a56bf1acd526c0f1aa16e95', '6b0796fa3374abcaec08976bf2aed071a2088b1d', 'df92b9111c10adb9b60b2b223ab54700b82fc043', '09ef54bf34fc31cb12543a8f7b8f812f1a1d6b5c', '4f3d784af6ada208a7adc5b264474eb00f0e7a5d', 'b22ad9555a79c6f45deeaa58c28f78a8cf0caa4d', 'df18b058058ee3c1370b8a465c2d3031fd274250', '509aac8bdba6d4c0c8ef7c2c59541dd3ece39c1c', '0da3046f1f964db135623c1d1364666f553b90cd', '7f2505750f87330ec9976a2738f45e052d9ec35a', '926902f6bc27a5d531cd211607f4ed86478dfc0d', '9ea7dfe3e38825d961b495690675dc245668a519', '0a7f7bc109d653df21cd9167dd4dd45f7a9a89d5', 'f6e2fd1cc73c5f5e4a1e9e3c15b4894bd6720a11', 'af9966d23a64fc3c36c121dd153f9aecb1e4d59f', 'efe6fba7d02ad06bec603b57f2e5115b7ccd31d8', '1c85669eb58fc986d43eb7c878e03cb58fb4883d', '6d154589224c490b532eec882776b059c884ae84', '64c2509b76c9755b190476a1c0fe233186842770', '5e50145f56201e01c61383c37b32577cd92c05e6', 'fb4c0ab6aff30711fceebef288d99b18c9b4d51c'])]
commits=[CommitInfo(commit_hash='700308b91a49af60d815f820287f330421036800', abbr_hash='700308b', tree='e445241aca9587413250deeda0be46f46b560ec3', parent='b8926be15d53a3a8a77962325df5c3d52a811a8e', refs='', subject='directory structure initialization', author_name='Gerardo De Luisi', author_email='deluisigerardo@gmail.com', date=date.fromtimestamp(time()), files=['main.py', 'pyproject.toml', 'src/_internal/__init__.py', 'src/app.py']),
         CommitInfo(commit_hash='b8926be15d53a3a8a77962325df5c3d52a811a8e', abbr_hash='b8926be', tree='fcce95b9b4c4e3c097f2600e709d1331aa43d271', parent='c38d21165cc5db6a345beee77adaa60691de0525', refs='', subject='Create python-app.yml', author_name='GeggeDL', author_email='102797969+GDeLuisi@users.noreply.github.com', date=date.fromtimestamp(time()), files=['.github/workflows/python-app.yml'])]

@fixture
def tree():
    fo=Folder("folder1",dict(file1=File("file1",10,"asdasdasd"),folder2=Folder("folder2",dict(),"kljfjf")),"kljklfjlfkj")
    fi=File("file2",size=12,hash_string="dsfdgds")
    return TreeStructure("sajdhasjdhk",[fo,fi])


def test_make_commits_dataframe():
    pd=make_commit_dataframe(commits)
    # logger.debug(pd.columns)
    assert True
def test_make_authors_dataframe():
    pd=make_author_dataframe(authors)

    assert True
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

def test_dataframes(tree):
    df1=tree.get_dataframe().sort_values("name").reset_index(drop=True)
    df2=tree.get("file2").get_dataframe()
    df3=tree.get("folder1").get_dataframe()
    df=pd.DataFrame(dict(name=[tree.base.name],size=[tree.base.get_size()],hash_string=[tree.base.hash_string]))
    df4=pd.concat([df,df2,df3]).sort_values("name").reset_index(drop=True)
    df1.sort_index(axis=1,inplace=True)
    df4.sort_index(axis=1,inplace=True)
    logger.debug(df1.head())
    logger.debug(df4.head())
    df1.info()
    df4.info()
    assert df1.equals(df4)