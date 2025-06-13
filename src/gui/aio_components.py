from dash import Output, Input, State, html, dcc, callback, MATCH,clientside_callback,ALL
import uuid
import dash_bootstrap_components as dbc
from repository_miner.data_typing import Author,CommitInfo
from typing import Iterable
from math import ceil
from src._internal.file_parser import DEFAULT_SATD_HIGHLIHGTER
import re
class AuthorDisplayerAIO(): 
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
            'aio_id': aio_id
        }
        listgroup =lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'listgroup',
            'aio_id': aio_id
        }
        store =lambda aio_id: {
            'component': 'AuthorDisplayerAIO',
            'subcomponent': 'store',
            'aio_id': aio_id
        }

    def __init__(
        self,
        author:Author,
        contributions:Iterable[str]=[],
        elements_per_page:int=5,
        text:str="",
        modal_props:dict=None,
        span_props:dict=None,
        div_props:dict=None,
        aio_id:str=None
    ):
        cont=list(sorted(contributions))
        num_pages=ceil(len(cont)/elements_per_page)
        commit_pages=ceil(len(author.commits_authored)/elements_per_page)
        if aio_id is None:
            aio_id = str(uuid.uuid4())
        sp_props= span_props.copy() if span_props else {}
        if "className" not in sp_props:
            sp_props["className"]="clickable"
            
        d_props =div_props.copy() if div_props else {}
        
        m_props = modal_props.copy() if modal_props else {}
        
        self.comp=html.Span([
            dcc.Store(id=self.ids.store(aio_id),data=dict(cont=cont,epg=elements_per_page)),
            dcc.Store(id=self.ids.store(aio_id+"_commit"),data=dict(epg=elements_per_page,cont=author.commits_authored)),
            dbc.Modal([
                dbc.ModalHeader([html.I(className="bi bi-person-circle h3 pe-3"),html.Span(f"{author.name} <{author.email}>",className="fw-bold")]),
                dbc.ModalBody([
                    dbc.Container([

                        html.H6([html.Span(f"Files Authored: ",className="fw-bold") ,str(len(cont))]),
                        html.H6([html.Span(f"Commits Authored: ",className="fw-bold") ,str(len(author.commits_authored))]),
                        html.H6(html.Span("Files authored list: ",className="fw-bold")),

                        dbc.Tabs([
                            dbc.Tab(
                                [
                                    dbc.Pagination(id=self.ids.pagination(aio_id=aio_id),max_value=num_pages,min_value=1,active_page=1,first_last=True, previous_next=True,fully_expanded=False),
                                    dbc.ListGroup(
                                        id=self.ids.listgroup(aio_id=aio_id)
                                    )
                                ] if cont else html.H5("No file authored")
                            ,label="Files Authored"),
                            dbc.Tab(
                                [
                                    dbc.Pagination(id=self.ids.pagination(aio_id=aio_id+"_commit"),max_value=commit_pages,min_value=1,active_page=1,first_last=True, previous_next=True,fully_expanded=False),
                                    dbc.ListGroup(
                                        id=self.ids.listgroup(aio_id=aio_id+"_commit")
                                    )
                                ]
                            ,label="Commits Authored")
                        ]),
                    ]),
                ])
            ],id=self.ids.modal(aio_id),**m_props),
            html.Span(id=self.ids.button(aio_id),children=f"{author.name} {text}",**sp_props)])
            
    def create_comp(self)->html.Span:
        return self.comp 

    clientside_callback(
    """
    function(_,) {
        return {'is_open':true};
    }
    """,
    Output(ids.modal(MATCH), 'is_open'),
    Input(ids.button(MATCH), 'n_clicks'),
    prevent_initial_call=True
    )
    
    clientside_callback(
    """
    function(_, data) {
        const cont=data.cont;
        const epg=data.epg;
        const slicer=epg*(_-1);
        const to_show=cont.slice(slicer,slicer+epg);
        var lis=[];
        to_show.forEach((c)=>{
            lis.push({'type': 'ListGroupItem', 'namespace': 'dash_bootstrap_components', 'props': {'children': c}})
        });
        return lis;
    }
    """,
    Output(ids.listgroup(MATCH), 'children'),
    Input(ids.pagination(MATCH), 'active_page'),
    State(ids.store(MATCH),"data")
    )

class SATDDisplayerAIO(): 
    class satd_ids:
        modal = lambda satd_id: {
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'modal',
            'satd_id': satd_id
        }
        button = lambda satd_id: {
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'button',
            'satd_id': satd_id
        }
        content =lambda satd_id: {
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'content',
            'satd_id': satd_id
        }
        table =lambda satd_id: {
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'table',
            'satd_id': satd_id
        }
        store =lambda satd_id: {
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'store',
            'satd_id': satd_id
        }
        
        table_data=lambda satd_id:{
            'component': 'SATDDisplayerAIO',
            'subcomponent': 'table_data',
            'satd_id': satd_id,
        }

    def __init__(
        self,
        file:str,
        satds:dict[int,str]={},
        text:str="",
        modal_props:dict=None,
        span_props:dict=None,
        div_props:dict=None,
        satd_id:str=None
    ):
        aio_id=satd_id
        if satd_id is None:
            aio_id = str(uuid.uuid4())
        sp_props= span_props.copy() if span_props else {}
        if "style" not in sp_props:
            sp_props["style"]=dict(cursor="pointer")
            
        d_props =div_props.copy() if div_props else {}
        
        m_props = modal_props.copy() if modal_props else {}
        table_header = [html.Thead(html.Tr([html.Th("Line"), html.Th("Type")]))]
        # satd_table_dict:dict[str,list[str]]=dict(type=list(),line=list(),content=list(),placeholder=list())
        rows=list()
        i=0
        for n,c in satds.items():
            c=c.strip()
            t,content="",""
            pattern=re.compile('|'.join(DEFAULT_SATD_HIGHLIHGTER))
            t=re.search(pattern,c).group()
            _,content=re.split(pattern,c,1)
            rows.append(html.Tr([html.Td(str(n),id=self.satd_ids.table_data(aio_id+f"_table_{str(i)}_line"),style={"cursor":"pointer"},className="fw-bold text-info"),
                                html.Td(t,id=self.satd_ids.table_data(aio_id+f"_table_{str(i)}_type")),
                                dbc.Modal([
                                    dbc.ModalBody([
                                        dbc.Container([
                                            html.P(id=self.satd_ids.content(aio_id+f"_table_{str(i)}_line"),style={"overflow": "hidden","word-wrap":"break-word"},children=content)
                                        ]),
                                    ])
                                ],id=self.satd_ids.modal(aio_id+f"_table_{str(i)}_line"),is_open=False,scrollable=True),
                                ]))
            i+=1
        table_body = [html.Tbody(rows,id=self.satd_ids.table(aio_id+"_table"))]
        table = dbc.Table(table_header + table_body, bordered=True,size="sm",)
        self.comp=html.P([
            dbc.Modal([
                dbc.ModalHeader([html.I(className="bi bi-wrench h3 pe-3"),html.Span(f"{file} SATDs",className="fw-bold")]),
                dbc.ModalBody([
                    dbc.Container([
                        html.H6([html.Span("SATDs found:",className="fw-bold") ,str(len(satds.keys()))]),
                        table
                        # dash_table.DataTable(satd_df,[{"name": "line", "id": "line"},{"name": "type", "id": "type"},{"name": "content", "id": "placeholder","presentation":"markdown"}],filter_action="native",sort_action="native", id=self.satd_ids.table(aio_id+"_table"),markdown_options={"html":True} ),
                    ]),
                ])
            ],id=self.satd_ids.modal(aio_id),**m_props),
            html.Span(id=self.satd_ids.button(aio_id),children=file,**sp_props),html.Span(text)
        ])
            
    def create_comp(self)->html.P:
        return self.comp 

    clientside_callback(
    """
    function(_,) {
        return {'is_open':true};
    }
    """,
    Output(satd_ids.modal(MATCH), 'is_open',allow_duplicate=True),
    Input(satd_ids.button(MATCH), 'n_clicks'),
    prevent_initial_call=True
    )
    
    clientside_callback(
    """
    function(_,) {
        return {'is_open':true};
    }
    """,
        Output(satd_ids.modal(MATCH), 'is_open',allow_duplicate=True),
        Input(satd_ids.table(MATCH), 'n_clicks'),
        prevent_initial_call=True
    )
    
    clientside_callback(
    """
    function(_) {
        return {'is_open':true};
    }
    """,
        Output(satd_ids.modal(MATCH), 'is_open'),
        Input(satd_ids.table_data(MATCH), 'n_clicks'),
        prevent_initial_call=True
    )

class CommitDisplayerAIO():
    class ids:
        modal = lambda aio_id: {
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'modal',
            'aio_id': aio_id
        }
        button = lambda aio_id,target: {
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'button',
            'aio_id': aio_id,
            'target':target
        }
        content =lambda aio_id,sub_id: {
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'content',
            'aio_id': aio_id,
            'sub_id':sub_id
        }
        table =lambda aio_id: {
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'table',
            'aio_id': aio_id
        }
        store =lambda aio_id: {
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'store',
            'aio_id': aio_id
        }
        
        table_data=lambda aio_id:{
            'component': 'CommitDisplayerAIO',
            'subcomponent': 'table_data',
            'aio_id': aio_id,
        }

    def __init__(
        self,
        commit:CommitInfo,
        text:str="",
        modal_props:dict=None,
        span_props:dict=None,
        div_props:dict=None,
        id:str=None
    ):
        aio_id=id
        if id is None:
            aio_id = str(uuid.uuid4())
        sp_props= span_props.copy() if span_props else {}
        if "className" not in sp_props:
            sp_props["className"]="clickable"
        d_props =div_props.copy() if div_props else {}
        m_props = modal_props.copy() if modal_props else {}        
        self.comp=html.Span([
            dbc.Modal([
                dbc.ModalHeader([html.I(className="bi bi-git h3 pe-3"),html.Span(f"Commit {commit.abbr_hash}",className="fw-bold")]),
                dbc.ModalBody([
                    dbc.Container([
                        html.P([html.Span("Commit Message: ",className="fw-bold"), commit.subject] ),
                        html.P([html.Span("Commit Author: ",className="fw-bold"), f"{commit.author_name} <{commit.author_email}>"]),
                        html.P([html.Span("Complete hash string: ",className="fw-bold"),commit.commit_hash]),
                        html.P([html.Span("Created at: ",className="fw-bold") ,commit.date.strftime(r"%d-%m-%Y")]),
                        
                    ]),
                ])
            ],id=self.ids.modal(aio_id),size="lg",**m_props),
            html.Span(id=self.ids.button(aio_id,"modal"),children=f"{commit.abbr_hash} {text}",**sp_props)
        ])
    def create_comp(self)->html.Span:
        return self.comp 

    clientside_callback(
    """
    function(_,) {
        return true;
    }
    """,
    Output(ids.modal(MATCH), 'is_open'),
    Input(ids.button(MATCH,"modal"), 'n_clicks'),
    prevent_initial_call=True
    )
