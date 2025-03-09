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
                html.Div(
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


stack=dbc.Stack(id="stack_info",className="p-2 h-75",children=[
        dbc.Card(
                dbc.CardBody(
                [
                        dbc.Row([
                                dbc.Col(
                                        children=[html.Div([dbc.Label(["Author Picker"]),dcc.Dropdown(id="author_picker",searchable=True,clearable=True,placeholder="Author name")]),],
                                        width=6),
                                dbc.Col(
                                                children=[html.Div([dbc.Label(["Author Email Picker"]),dcc.Dropdown(id="author_picker_email",searchable=True,disabled=True,clearable=True,placeholder="Author email")]),],
                                                width=6)
                                        
                                ]),
                                
                        dbc.Row([
                                dbc.Col(
                                        children=[html.Div([dbc.Label(["Degree of Authorship(DOA) threshold picker"]),dcc.Slider(id="doa_picker",min=0,max=1,step=0.1,value=0.75)]),],
                                        width=12),
                                ]),
                        dbc.Row([
                                dbc.Col(
                                        children=[dbc.Button(id="calculate_doa",children=["Calculate DOAs"],disabled=False)],
                                        width=12),
                                ]),
                ]
        ),
        ),
        dbc.Card(
                dcc.Loading([
                        dbc.CardBody(
                        [
                        html.H1(["Truck Factor"] ,className="card-title"),
                        html.Div(
                                id="truck-calculation-div",
                        )
                        ]
        ),
        ],overlay_style={"visibility":"visible", "filter": "blur(2px)"}
        ),
        )
        ,
        ],gap=2)

layout = dbc.Container([
        dcc.Store("authors_doas",data=dict()),
        dcc.Loading(id="dir_info_loader",display="show",fullscreen=True),
        dbc.Row([
                dbc.Col(
                        [
                        dcc.Loading(id="dir_treemap_loader",
                        children=[dcc.Graph("dir_treemap",className="h-75")],
                        )
                        ]
                ,width=10,align="center"),
                dbc.Col(
                        [stack],
                        width=2,align="center"
                )
                ]),
                
                ]
                ,fluid=True)
        

@callback(
        Output("dir_treemap","figure"),
        Input("calculate_doa","n_clicks"),
        Input("branch_picker","value"),
        State("author_picker","value"),
        State("author_picker_email","value"),
        State("doa_picker","value"),
        State("repo_path","data"),
        State("contribution_cache","data"),
)
def populate_treemap(_,b,name,email,doa,data,cache):
        # df=pd.DataFrame(cache)
        rp=RepoMiner(data)
        author_doas=None
        if name and email:
                author=f"{name}{email}"
                author_doas=cache[author]

        tree = rp.get_dir_structure(b)
        df=tree.get_treemap()
        # print(df)
        df=pd.DataFrame(df)
        
        if author_doas:
                # print(author_doas)
                files=[k for k,v in author_doas.items() if v>=doa]
                doas=set()
                for f in files:
                        ps=Path(f).parts
                        for part in ps:
                                doas.add(part)
                # print(doas)
                df=df.loc[df["name"].isin(doas)].reset_index(drop=True)
                # print(df.head())
        fig=px.treemap(data_frame=df,parents=df["parent"],names=df["name"],ids=df["child"],color_discrete_map={'(?)':'lightgrey', 'file':'paleturquoise', 'folder':'crimson'},color=df["type"],custom_data=["id","type"],maxdepth=2,height=800)
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
        Output("sidebar_info", "is_open"),
        Input("open_info", "n_clicks"),
        [State("sidebar_info", "is_open")],
)
def toggle_offcanvas(n1, is_open):
        if n1:
                return not is_open
        return is_open

# @callback(
#         Output("author_doas","data"),
#         Input("calculate_doa","n_clicks"),
#         State("author_picker","value"),
#         State("doa_picker","value"),
#         State("branch_picker","value"),
#         State("repo_path","data"),
# )
# def calculate_author_DOA(_,auth,doa_th,branch,path,cache):
#         if auth in cache:
                
#         set_props("dir_treemap_loader",{"display":"show"})
#         rp=RepoMiner(repo_path=path)
        
#         rp.get_author_files(auth,branch,doa_th)
#         set_props("dir_treemap_loader",{"display":"auto"})
        
#         return None if auth else no_update


@callback(
        Output("author_picker","options"),
        Input("authors_cache","data"),
)
def populate_author_picker(cache):
        authors_df=pd.DataFrame(cache)
        return authors_df["name"].unique().tolist()

@callback(
        Output("author_picker_email","options"),
        Output("author_picker_email","disabled"),
        Input("author_picker","value"),
        State("authors_cache","data"),
)
def populate_author_picker(name,cache):
        if name:
                authors_df=pd.DataFrame(cache)
                authors_df=authors_df.loc[authors_df["name"]==name]
                return authors_df["email"].unique().tolist(),False
        else:
                return no_update,True

@callback(
        Output("calculate_doa","disabled"),
        Input("author_picker_email","value"),
)
def populate_author_picker(val):
        return val==None