from src.utility import filter
from typing import Any
import re
@filter("equal")
def equal(value:Any,comparison:Any)->bool:
    # print(value==comparison)
    return value==comparison

@filter("like")
def like(value:str,comparison:str)->bool:
    # print(value==comparison)
    return re.match(f'^{comparison}.*',value) != None

@filter("smaller")
def smaller(value:float,comparison:float)->bool:
    # print(value==comparison)
    return value<comparison

@filter("greater")
def greater(value:float,comparison:float)->bool:
    # print(value==comparison)
    return value==comparison
