from dash import Dash, Output, Input, State, html, dcc, callback, MATCH,clientside_callback
import uuid
import dash_bootstrap_components as dbc
from src._internal import Author
from typing import Iterable
from math import ceil
import json

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
        if "style" not in sp_props:
            sp_props["style"]=dict(cursor="pointer")
            
        d_props =div_props.copy() if div_props else {}
        
        m_props = modal_props.copy() if modal_props else {}
        
        self.comp=html.Span([
            dcc.Store(id=self.ids.store(aio_id),data=dict(cont=cont,epg=elements_per_page)),
            dcc.Store(id=self.ids.store(aio_id+"_commit"),data=dict(epg=elements_per_page,cont=author.commits_authored)),
            dbc.Modal([
                dbc.ModalHeader([html.I(className="bi bi-person-circle h3 pe-3"),html.Span(f"{author.name} <{author.email}>",className="fw-bold")]),
                dbc.ModalBody([
                    dbc.Container([
                        html.H6(f"Files Authored: {len(cont)}"),
                        html.H6(f"Commits Authored: {len(author.commits_authored)}"),
                        html.H6(f"Files authored list:"),
                        dbc.Tabs([
                            dbc.Tab(
                                [
                                    dbc.Pagination(id=self.ids.pagination(aio_id=aio_id),max_value=num_pages,min_value=1,active_page=1,first_last=True, previous_next=True,fully_expanded=False),
                                    dbc.ListGroup(
                                        id=self.ids.listgroup(aio_id=aio_id)
                                    )
                                ]
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
            html.Span(id=self.ids.button(aio_id),children=f"{author.name} <{author.email}> ",**sp_props),html.Span(text)
        ])
            
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

