import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx
from src._internal import RepoMiner,make_commit_dataframe,prune_common_commits,getMaxMinMarks,unixTimeMillis,unixToDatetime
import dash.html as html
from datetime import date
from src.gui.components import sidebar
import plotly.express as px
import pandas as pd
from pathlib import Path
from src._internal.data_typing import Author,CommitInfo,TreeStructure,File,Folder
import dash_bootstrap_components as dbc
from io import StringIO
import json
import time
from logging import getLogger
logger=getLogger("mainpage")
dash.register_page(__name__,"/dir")
#TODO create a card on the right side of the screen showing info about the chosen file and authorship
#TODO create a Author choice panel from which DOA thresholds can be chosen with the chosen author

file_cards = [
        dbc.Card(
        dbc.CardBody(
                [
                html.H4( id="file-description-title",className="card-title"),
                html.P(
                        id="file-description-text",
                        className="card-text",
                )
                ]
        ),
        ),
        dbc.Card(
        dbc.CardBody(
                [
                html.H4( ["File Authors"],id="authors-description-title",className="card-title"),
                html.P(
                        id="authors-description-text",
                        className="card-text",
                )
                ]
        ),
        ),
        dbc.Card(
        dbc.CardBody(
                [
                html.H4(["Thresholding"] ,id="thresholding-description-title",className="card-title"),
                html.Div(
                        id="thresholding-div",
                )
                ]
        ),
        ),
        
]

sideb=dbc.Stack(className="bg-secondary bg-opacity-25 rounded-2 p-2 h-75",gap=2)
sideb.children=file_cards

layout = dbc.Container([
        dcc.Store("file-info-store"),
        dcc.Loading(id="dir_info_loader",display="show",fullscreen=True),
        dbc.Modal(
                [
                dbc.ModalHeader(dbc.ModalTitle("Test",id="modal_title")),
                dbc.ModalBody(id="modal_body"),
                ],
                id="test-div",
                scrollable=True,
                fullscreen=True,
                is_open=False,
                ),
        dbc.Row([
                dbc.Col(
                        [
                        dcc.Loading(id="dir_treemap_loader",
                        children=[dcc.Graph("dir_treemap",className="h-75")],
                        )
                        ]
                ,width=10,align="center"),
                dbc.Col(
                sideb
                ,width=2)
                ]),
                ]
                ,fluid=True)
        

@callback(
        Output("dir_treemap","figure"),
        Input("branch_picker","value"),
        State("repo_path","data")
)
def populate_treemap(b,data):
        # df=pd.DataFrame(cache)
        rp=RepoMiner(data)
        tree = rp.get_dir_structure(b)
        df=tree.get_treemap()
        fig=px.treemap(data_frame=pd.DataFrame(df),parents=df["parent"],names=df["name"],ids=df["child"],color_discrete_map={'(?)':'lightgrey', 'file':'paleturquoise', 'folder':'crimson'},color=df["type"],custom_data=["id","type"],height=800)
        fig.update_layout(
        uniformtext=dict(minsize=10),
        margin = dict(t=50, l=25, r=25, b=25)
        )
        set_props("dir_info_loader",{"display":"auto"})
        # fig=px.treemap(parents = ["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve","Noam"],names = ["Eve","Cain", "Seth", "Enos/Noam", "Noam", "Abel", "Awan", "Enoch", "Azura","Aqua"],)
        return fig

# @callback(
#         Output("modal_body","children"),
#         Output("modal_title","children"),
#         Output("test-div", "is_open"),
#         Input("dir_treemap","clickData"),
#         State("repo_path","data"),
        
# )
# def list_to_file_click(data,repo_path):
#         if not data:
#                 return no_update,no_update,no_update
#         hash_string,tp=data["points"][0]["customdata"]
#         if tp != "file":
#                 return no_update,no_update,no_update
#         rp=RepoMiner(repo_path)
#         text=rp.get_source(hash_string)
#         # print(data)
#         return [html.Div([line]) for line in text],[data["points"][0]["label"]],True

@callback(
        Output("file-info-store","data"),
        Input("dir_treemap","clickData"),
        State("repo_path","data"),
        State("file-info-store","data"),
)
def load_file_info(f_data,repo_path,cache):
        if cache["id"]==f_data["points"][0]["id"]:
                return no_update
        