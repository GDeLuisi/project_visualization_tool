from dash.dcc import DatePickerRange,Graph
from dash import html,Input,Output,callback
from plotly.express import density_heatmap
from plotly.graph_objects import Figure
from git import Commit
from datetime import date
from typing import Literal
from src._internal import Author
import pandas as pd
from typing import Iterable,Callable,Optional
import dash_bootstrap_components as dbc
from dash import Input,Output,MATCH
from math import ceil

def get_author_overview_button(author:Author,contributions:Iterable[str]=[],rows_per_page:int=5)->html.Span:
    cont=list(contributions)
    pages_count=ceil(len(cont)/rows_per_page)
    retdiv=html.Span([
        dbc.Modal([
            dbc.ModalHeader([html.I(className="bi bi-person-circle h3 pe-3"),html.Span(f"{author.name} <{author.email}>",className="fw-bold")]),
            dbc.ModalBody([
                dbc.Container([
                    html.Br(),
                    html.H6(f"Files Authored: {len(cont)}"),
                    html.H6(f"Commits Authored: {len(author.commits_authored)}"),
                    # dbc.Pagination(max_value=pages_count,min_value=1,first_last=True, previous_next=True,fully_expanded=False),
                    # dbc.ListGroup(
                    #     [
                            
                    #     ]
                    # )
                ])
            ])],
            id={"type":"author_modal","index":f"{author.name}|{author.email}"}),
        html.Span(id={"type":"author_modal_btn","index":f"{author.name}|{author.email}"},children=f"{author.name} <{author.email}>",className="fw-bold ",style={"cursor":"pointer"})
    ])
    return retdiv
    
    
    