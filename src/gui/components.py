
from dash import Dash, Output, Input, State, html, dcc, callback, MATCH,clientside_callback,dash_table,ALL,no_update
import uuid
import dash_bootstrap_components as dbc
from src._internal import Author
from typing import Iterable,Union
from math import ceil
import json
import pandas as pd
import re

class CustomTable():
    class ids:
        modal = lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'modal',
            'aio_id': aio_id
        }
        button = lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'button',
            'aio_id': aio_id
        }
        pagination =lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'pagination',
            'aio_id': aio_id,
        }
        table =lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'table',
            'aio_id': aio_id
        }
        store =lambda aio_id,sub_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'store',
            'aio_id': aio_id,
            'sub_id':sub_id
        }
        
    def __init__(
        self,
        data:Union[dict[str,list]|list[dict[str]]],
        elements_per_page:int=5,
        div_props:dict=None,
        table_props:dict=None,
        id:str=None,
    ):
        data_to_use:list[dict[str]]=list()
        keys=None
        ln=0
        if isinstance(data,dict):
            keys=list(data.keys())
            key=keys.pop()
            keys.add(key)
            ln=len(data[k])
            #check for equal length in data lists
            for k,v in data.items():
                if not isinstance(v,list):
                    raise TypeError("The shape of dictionary must be dict[str,list] or list[dict[str]]")

            for i in range(ln):
                nd=dict()
                for k in data.keys():
                    try:
                        nd[k]=data[k][i]
                    except IndexError:
                        raise ValueError("All data must have the same length")
                data_to_use.append(nd)
                
        elif isinstance(data,list):
            ln=len(data)
            if not data:
                raise ValueError("Cannot compute an empty list")
            keys=list(data[0].keys())
            for d in data:
                if not isinstance(d,dict):
                    raise TypeError("The shape of dictionary must be dict[str,list] or list[dict[str]]")
                if list(d.keys()) != keys:
                    raise ValueError("All data must have the same keys")
            data_to_use=data
        
        num_pages=ceil(ln/elements_per_page)
        if id is None:
            id = str(uuid.uuid4())
        d_props =div_props.copy() if div_props else {}
        t_props =table_props.copy() if table_props else {}

        table = dbc.Table([],id=self.ids.table(id),**t_props)
        self.comp=dbc.Container([
            dcc.Store(id=self.ids.store(id,"rows"),data=data_to_use),
            dcc.Store(id=self.ids.store(id,"pagination"),data=dict(num_pages=num_pages,epg=elements_per_page)),
            dbc.Pagination(id=self.ids.pagination(id),min_value=1,max_value=num_pages,active_page=1),
            table
        ],**d_props)
        
    def create_comp(self):
        return self.comp

    @callback(
        Output(ids.table(MATCH), 'children'),
        Input(ids.pagination(MATCH), 'active_page'),
        State(ids.store(MATCH,"pagination"), 'data'),
        State(ids.store(MATCH,"rows"),"data")
    )
    def populate_table(page,pag_data,data):
        if not (pag_data and data):
            return no_update
        epg=pag_data["epg"]
        index=epg*(page-1)
        keys=sorted(list(data[0].keys()))
        table_header = [html.Thead(html.Tr([html.Th(" ".join(header.split("_")).capitalize()) for header in keys]))]
        rows:list[html.Tr]=list()
        for d in data[index:index+epg]:
            rows.append(html.Tr([html.Td(d[k]) for k in keys]))
        table_body = [html.Tbody(rows)]
        return table_header+table_body
