from src.utility import filter,sorter
from typing import Any,Iterable
import re
from datetime import datetime
@filter("equal")
def equal(value:Any,comparison:Any)->bool:
    # print(value==comparison)
    if not value:
        return True
    return value==comparison

@filter("like")
def like(value:str,comparison:str)->bool:
    # print(value==comparison)
    if not value:
        return True
    return re.match(f'^{value}.*',comparison) != None

@filter("smaller")
def smaller(value:float,comparison:float)->bool:
    # print(value==comparison)
    if value==None:
        return True
    return value<comparison

@filter("greater")
def greater(value:float,comparison:float)->bool:
    if value==None:
        return True
    # print(value==comparison)
    return value>comparison

@sorter("date")
def sort_dates(values:Iterable,key,reverse:bool=False):
    # value_list:list[datetime]=list()
    # for v in values:
    #     year=""
    #     month=""
    #     day=""
    #     for i,match in enumerate(re.match(r'\d+',key(v)).groups(),1):
    #         if len(match)==4:
    #             year = match
    #         elif int(match)<12 and i==2:
    #             month = match
    #         else:
    #             day = match
    #     value_list.append(datetime.fromisoformat(f"{year}-{month}-{day}"))
    value_list=list(values)
    value_list.sort(reverse=reverse,key=lambda v: datetime.strptime(key(v),r"%d-%m-%Y"))
    return value_list