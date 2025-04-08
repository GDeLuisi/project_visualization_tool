from logging import getLogger
from typing import Iterable,Literal,Union,Callable
from math import log1p
import json
import pandas as pd
import unicodedata
logger=getLogger("helper")

def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0]!="C")

def infer_programming_language(files:Iterable[str],threshold:float=0.35)->list[str]:
        suffix_count:dict[str,int]=dict()
        fs=set(files)
        tot_files=len(fs)
        ret_suffixes=list()
        for file in fs:
            try:
                suffix=file.rsplit(".",maxsplit=1)[1]
                if suffix not in suffix_count:
                    suffix_count[suffix]=0
                suffix_count[suffix]+=1
            except IndexError:
                pass
        for suff,count in suffix_count.items():
            logger.debug(f"Found suffix {suff} {count} times on {tot_files} files")
            if float(count/tot_files) >= threshold:
                ret_suffixes.append("."+suff)
        return ret_suffixes

class DataFrameAdapter():
    def __init__(self):
        pass
    def get_dataframe(self)->pd.DataFrame:
        var_dict=self.__dict__.copy()
        for k,v in var_dict.items():
            var_dict[k]=[v]
        df=pd.DataFrame(var_dict)
        return df        
class JSONSerializebleAdapter():
    def __init__(self):
        pass
    def JSON_serialize(self,type:Literal["dict","str"]="dict")->Union[dict,str]:
        if type not in ["dict","str"]:
            raise TypeError()
        var_dict=self.__dict__.copy()
        for k,v in var_dict.items():
            if isinstance(v,JSONSerializebleAdapter):
                var_dict[k]=v.JSON_serialize()
        if type=="str":
            var_dict=json.dumps(var_dict)
        return var_dict
    
class LazyLoader():
    def next(self):
        raise NotImplementedError()
    
class Singleton(type):
    loaders_registry=dict()
    def __call__(cls, *args, **kwargs):
        if cls not in cls.loaders_registry:
            # print(f"{cls} not found")
            instance = super().__call__(*args, **kwargs)
            cls.loaders_registry[cls] = instance
        return cls.loaders_registry[cls]
    def __exist__(instance)->bool:
        return instance in Singleton.loaders_registry
    def __delete__(instance):
        Singleton.loaders_registry.pop(instance)

