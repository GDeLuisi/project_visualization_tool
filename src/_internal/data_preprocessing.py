import pandas as pd
from typing import Iterable
# from inspect import get_annotations
from src._internal.data_typing import Author
from time import strftime,gmtime
from datetime import date
from functools import cache
from logging import getLogger
import time
from datetime import datetime
logger=getLogger("Data Preprocessing")

def unixTimeMillis(dt:pd.Timestamp):
    ''' Convert datetime to unix timestamp '''
    return int(dt.timestamp())

def unixToDatetime(unix:int)->pd.Timestamp:
    ''' Convert unix timestamp to datetime. '''
    return pd.to_datetime(unix,unit='s',utc=True)
def getMaxMinMarks(start_date:pd.Timestamp,end_date:pd.Timestamp):
    ''' Returns the marks for labeling. 
    '''
    date_format='%Y-%m-%d'
    result={}
    result[unixTimeMillis(start_date)] = str(start_date.strftime(date_format))
    result[unixTimeMillis(end_date)] = str(end_date.strftime(date_format))
    return result
def getMarks(dates:Iterable[pd.Timestamp], Nth=100):
    ''' Returns the marks for labeling. 
        Every Nth value will be used.
    '''

    result = {}
    for i, date in enumerate(dates):
        if(i%Nth == 1):
            # Append value to dict
            result[unixTimeMillis(date)] = str(date.strftime('%Y-%m-%d'))
    return result