from dash import Dash, Output, Input, State, html, dcc, callback, MATCH,clientside_callback,dash_table,ALL,no_update,ctx
import uuid
import dash_bootstrap_components as dbc
from src._internal import Author
from typing import Iterable,Union,Callable,Optional
from math import ceil
from src.utility.filters import FilterFactory,Filter,sorter_provider
import src.gui.filters
import json
import pandas as pd
import re
from logging import getLogger

logger = getLogger("components_logger")

class CustomTable():
    class ids:
        modal = lambda aio_id: {
            'component': 'CustomTable',
            'subcomponent': 'modal',
            'aio_id': aio_id
        }
        button = lambda aio_id,target,purpose: {
            'component': 'CustomTable',
            'subcomponent': 'button',
            'aio_id': aio_id,
            'target': target,
            'purpose': purpose
        }
        pagination =lambda aio_id: {
            'component': 'CustomTable',
            'subcomponent': 'pagination',
            'aio_id': aio_id,
        }
        table =lambda aio_id: {
            'component': 'CustomTable',
            'subcomponent': 'table',
            'aio_id': aio_id
        }
        store =lambda aio_id,sub_id: {
            'component': 'CustomTable',
            'subcomponent': 'store',
            'aio_id': aio_id,
            'sub_id':sub_id
        }
        input= lambda aio_id,sub_id,target: {
            'component': 'CustomTable',
            'subcomponent': 'input',
            'aio_id': aio_id,
            'sub_id':sub_id,
            'target':target
        }
        
    def __init__(
        self,
        data:Union[dict[str,list]|list[dict[str]]],
        filters:dict[str,str]=None,
        sort:dict[str,str]=None,
        elements_per_page:int=5,
        div_props:dict=None,
        table_props:dict=None,
        id:str=None,
    ):
        data_to_use:list[dict[str]]=list()
        keys=None
        ln=0
        if isinstance(data,dict):
            keys=sorted(list(data.keys()))
            key=keys.pop()
            keys.add(key)
            ln=len(data[key])
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
            keys=sorted(data[0].keys())
            for d in data:
                if not isinstance(d,dict):
                    raise TypeError("The shape of dictionary must be dict[str,list] or list[dict[str]]")
                if set(d.keys()) != set(keys):
                    raise ValueError("All data must have the same keys")
            data_to_use=data
        
        num_pages=ceil(ln/elements_per_page)
        if id is None:
            id = str(uuid.uuid4())
        d_props =div_props.copy() if div_props else {}
        t_props =table_props.copy() if table_props else {}
        
        
        table_header = [html.Thead(html.Tr([html.Th([
            html.Span(" ".join(header.split("_")).capitalize(),className="pe-2"),
            html.I(className="bi bi-funnel clickable",id=self.ids.button(id,header,"filter"),n_clicks=0) if filters and header in filters else "",
            dbc.Collapse([
                dbc.Row(
                    [
                        dbc.Col([
                            dbc.Input(id=self.ids.input(id,"text",header),placeholder="Filter",size="md")
                            ],width=10),
                        dbc.Col([
                            html.I(className="bi bi-x-lg clickable",id=self.ids.button(id,header,"filter_clear"),n_clicks=0)
                            ],width=2,align="center")
                        ]),
                ],id=self.ids.input(id,"collapse",header),is_open=False) if filters and header in filters else "",
            html.I(className="bi bi-caret-down clickable",id=self.ids.button(id,header,"sort"),n_clicks=0) if sort and  header in sort else "",
            ]) for header in keys]))]
        
        table = dbc.Table(table_header,id=self.ids.table(id),**t_props)
        self.comp=dbc.Container([
            dcc.Store(id=self.ids.store(id,"filters"),data={"filters":filters,"sorters":sort}),
            dcc.Store(id=self.ids.store(id,"filtered_indexes"),data=list(range(len(data_to_use)))),
            dcc.Store(id=self.ids.store(id,"full_data"),data=data_to_use),
            dcc.Store(id=self.ids.store(id,"pagination"),data=dict(epg=elements_per_page)),
            dbc.Pagination(id=self.ids.pagination(id),min_value=1,max_value=num_pages,active_page=1,first_last=True,previous_next=True,fully_expanded=False),
            table
        ],**d_props)

        
    def create_comp(self):
        return self.comp

    @callback(
        Output(ids.table(MATCH), 'children'),
        Output(ids.pagination(MATCH), 'max_value'),
        Input(ids.pagination(MATCH), 'active_page'),
        Input(ids.store(MATCH,"filtered_indexes"),"data"),
        Input(ids.store(MATCH,"full_data"),"data"),
        State(ids.store(MATCH,"pagination"), 'data'),
        State(ids.table(MATCH), 'children'),
    )
    def populate_table(page,filtered_indexes:list[int],data,pag_data,table_data):
        # print(table_data[0])
        if not (pag_data and data):
            return no_update
        data_to_show=list()
        logger.debug(f"Filter indexes for population",extra={"component":"CustomTable","data":filtered_indexes})
        for i in filtered_indexes:
            data_to_show.append(data[i])
        epg=pag_data["epg"]
        index=epg*(page-1)
        rows:list[html.Tr]=list()
        if data_to_show:
            keys=sorted(data_to_show[0].keys())
            for d in data_to_show[index:index+epg]:
                rows.append(html.Tr([html.Td(d[k]) for k in keys]))
        else:
            rows.append("no data")
        table_body = [table_data[0],html.Tbody(rows)]
        return table_body,ceil(len(data_to_show)/epg)
    

    clientside_callback(
        """
        function(_){
            if(_== undefined){
                return window.dash_clientside.no_update;
            }
            const is_open=_%2==1;
            var collapse_control=  is_open ? ['bi bi-funnel-fill clickable',is_open] : ['bi bi-funnel clickable',is_open];
            return collapse_control;
            }   
        """,
        Output(ids.button(MATCH,MATCH,"filter"), 'className'),
        Output(ids.input(MATCH,"collapse",MATCH), 'is_open'),
        Input(ids.button(MATCH,MATCH,"filter"), 'n_clicks'),
    )
    
    @callback(
        Output(ids.store(MATCH,"filtered_indexes"),"data"),
        Input(ids.input(MATCH,"text",ALL), 'value'),
        State(ids.store(MATCH,"full_data"),"data"),
        State(ids.store(MATCH,"filters"), 'data'),
        State(ids.input(MATCH,"text",ALL), 'id'),
        prevent_initial_call=True
    )
    def filter_data(text,orig_data,filters,in_id):
        print(ctx.triggered_id)
        if not in_id[0] or not text:
            return no_update
        filtered_indexes=set()
        text_dict=dict()
        filter_dict:dict[str,Filter]=dict()
        for t,id_dict in zip(text,in_id):
            text_dict[id_dict["target"]]=t
            filter_dict[id_dict["target"]]=FilterFactory.create_filter(filters["filters"][id_dict["target"]])
        for i,d in enumerate(orig_data):
            for target,text_to_use in text_dict.items():
                filter=filter_dict[target]
                res=filter.fun(text_to_use,d[target])
                # logger.debug(f"Filter result for {target} is {res} ",extra={"component":"CustomTable"})
                if res:
                    filtered_indexes.add(i)
                else:
                    filtered_indexes.discard(i)
                    break
        filtered_indexes=list(filtered_indexes)
        logger.debug(f"Filter indexes from filter callback",extra={"component":"CustomTable","data":filtered_indexes})
        return filtered_indexes
    
    clientside_callback(
        """
        function(_){
            if(_== undefined){
                return window.dash_clientside.no_update;
            }
            const up=_%2==1;
            var collapse_control=  up ? 'bi bi-caret-up clickable' : 'bi bi-caret-down clickable';
            return collapse_control;
            }   
        """,
        Output(ids.button(MATCH,MATCH,"sort"), 'className'),
        Input(ids.button(MATCH,MATCH,"sort"), 'n_clicks'),
    )
    
    clientside_callback(
        """
        function(_){
            if(_== undefined){
                return window.dash_clientside.no_update;
            }
            return "";
            }   
        """,
        Output(ids.input(MATCH,"text",MATCH), 'value'),
        Input(ids.button(MATCH,MATCH,"filter_clear"), 'n_clicks'),
        prevent_initial_call=True
    )

    @callback(
        Output(ids.store(MATCH,"full_data"),"data"),
        Input(ids.button(MATCH,ALL,"sort"),"n_clicks"),
        State(ids.store(MATCH,"full_data"),"data"),
        State(ids.store(MATCH,"filters"), 'data'),
        prevent_initial_call=True
    )
    def sort_data(_,data,filters):
        if data==None or _==None or _==0:
            return no_update
        target=ctx.triggered_id["target"]
        # ids=btn_id
        logger.debug(f"Sort: {target}",extra={"component":"CustomTable","data":data[0][target]})
        sorter = sorter_provider(filters["sorters"][target])
        reverse=_[0]%2==0
        logger.debug(f"Chose sorter: {filters['sorters'][target]}",extra={"component":"CustomTable"})
        if not sorter:
            sorted_data=sorted(data,key=lambda d: d[target],reverse=reverse)
        else:
            sorted_data=list(sorter(data,lambda d:d[target],reverse))
        # print([d["Email"] for d in sorted_data])
        return sorted_data

