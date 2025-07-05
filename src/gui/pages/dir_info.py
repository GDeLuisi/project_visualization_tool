import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx,ALL,MATCH
import dash.html as html
from datetime import date
import plotly.express as px
import pandas as pd
from pathlib import Path
from repository_miner import RepoMiner,GitCmdError
from truck_factor_gdeluisi.main import infer_programming_language,resolve_programming_languages
import dash_bootstrap_components as dbc
from io import StringIO
from src.app.helper import build_tree_structure,retrieve_SATDs
import json
import time
from typing import Union
from src._internal.file_parser import DEFAULT_SATD_HIGHLIHGTER
from logging import getLogger
from src.gui import SATDDisplayerAIO
from math import ceil
logger=getLogger("mainpage")
dash.register_page(__name__,"/dir")
items_per_page=5 #TODO make it configurable by user
stack=dbc.Stack(id="stack_info",className="p-2 h-75",children=[
        
        dbc.Card(
                id="setd_files_info",
                children=[
                        dbc.CardHeader(id="setd_files_header",children="SATD discovery"),
                dbc.CardBody(
                        [
                        dbc.Container([
                                dcc.Loading([
                                dbc.Pagination(id="satd_pagination",min_value=1,max_value=1,fully_expanded=False,first_last=True,previous_next=True,active_page=1),
                                dbc.ListGroup(
                                        id="satd_files",children=[
                                                html.Br(),
                                                html.Br(),
                                                html.Br(),
                                        ]
                                ,flush=True,class_name="text-center")
                        ]
                        )
                        ,]
                                ),
                        ])
                        
                ],
        ),
        dbc.Button(id="graph_filtering_collapse_btn",children="Toggle directory filtering"),
        dbc.Collapse([
                dbc.Card([
                dbc.CardHeader([
                        "Graph filtering"
                        ]),
                dbc.CardBody(
                [
                        dbc.Row([
                                dbc.Col(
                                        children=[html.Div([dbc.Label(["Author Picker"]),dcc.Dropdown(id="author_picker",searchable=True,clearable=True,placeholder="Author name")]),],
                                        width=12),
                                        
                                ],className="py-2"),
                        dbc.Row([
                                dbc.Col(
                                        children=[html.Div([dbc.Label(["Degree of Authorship(DOA) threshold picker"]),dcc.Slider(id="doa_picker",min=0,max=1,included=True,step=0.05,value=0.75,marks={"0":"0","1":"1","0.75":"0.75","0.5":"0.5","0.25":"0.25",},tooltip={"placement":"bottom","always_visible":True})]),],
                                        width=12),
                                ],className="py-2"),
                        dbc.Row([
                                dbc.Col(
                                        children=[dbc.Button(id="calculate_doa",children=["Calculate DOAs"],disabled=False)],
                                        width=6),
                                dbc.Col(
                                        children=[dbc.Button(id="reset_doa",children=["Reset"])],
                                        width=6),
                                ],className="py-2",justify="center"),
                ]
                ),]
                ),
        ],"graph_filtering_collapse",is_open=False),
        dbc.Card(
                id="card-file-info",
                children=[
                        dbc.CardHeader(id="file-info-header"),
                        dbc.CardBody(
                        [
                                dcc.Loading([
                                html.Div(
                                        id="file-info",
                                )],overlay_style={"visibility":"visible", "filter": "blur(2px)"}
                                ),
                        ]
                        ),
                ],
                className="invisible"
        ),
        ],gap=2)

layout = dbc.Container([
        dcc.Store("authors_doas",data=dict()),
        dcc.Store("file_cache",data=dict()),
        dcc.Store("file_info_cache",data=dict()),
        dcc.Store("satd_files_cache",data=list()),
        dcc.Loading(id="dir_info_loader",display="show",fullscreen=True),
        dbc.Row([
                html.H1("Directory Tree Analysis",className="fw-bold h2 px-4"),
                dbc.Col(
                        [
                        dcc.Loading(id="dir_treemap_loader",
                        children=[
                                dcc.Graph("dir_treemap",className="h-75")
                                ],
                        )
                        ]
                ,width=9,align="center"),
                dbc.Col(
                        [stack],
                        width=3,align="center"
                )
                ]),
                
                ]
                ,fluid=True)

@callback(
        Output("graph_filtering_collapse","is_open"),
        Input("graph_filtering_collapse_btn","n_clicks"),
        prevent_initial_call=True
)
def open_graph_filtering_collapse(_):
        if _%2>0:
                return True
        return False


@callback(
        Output("satd_pagination","max_value"),
        Output("satd_files","children"),
        Output("satd_files_cache","data"),
        Input("satd_pagination","active_page"),
        Input("satd_files_cache","data"),
        State("repo_path","data"),
        prevent_intial_call=True
)
def populate_satd_list(page,cache:dict,path):
        # print("active")
        if not cache:
                rp=RepoMiner(path)
                highlighters=set(DEFAULT_SATD_HIGHLIHGTER)
                satds=retrieve_SATDs(rp,highlighters)
                cache=satds
        buttons:list[dbc.ListGroupItem]=list()
        keys=sorted(list(cache.keys()),reverse=True)
        start_value=(page-1)*items_per_page
        to_add=keys[start_value:start_value+items_per_page]
        for key in to_add:
                buttons.append(dbc.ListGroupItem(SATDDisplayerAIO(key,cache[key],span_props=dict(className="fw-bold ",style={"cursor":"pointer"}),modal_props={"scrollable":True}).create_comp()))
        return ceil(len(cache)/items_per_page),buttons,satds

@callback(
        Output({"type":"setd_modal","index":MATCH},"is_open"),
        Input({"type":"setd_button","index":MATCH},"n_clicks"),
        prevent_initial_call=True
)
def load_modal(_):
        #load setd modal on file_setd button click
        if _==0:
                return no_update
        return True

@callback(
        Output("file_info_cache","data"),
        Output("dir_treemap","figure"),
        Input("calculate_doa","n_clicks"),
        Input("branch_picker","value"),
        Input("tag_picker","value"),
        Input("contribution_cache","data"),
        State("author_picker","value"),
        State("doa_picker","value"),
        State("repo_path","data"),
)
def populate_treemap(_,b,t,cache,name,doa,data):
        # df=pd.DataFrame(cache)
        if not cache:
                return no_update,no_update
        rp=RepoMiner(data)
        author_doas=None
        tree_dict:dict[str,str]=dict()
        contributions=pd.DataFrame(cache)
        author_doas:pd.DataFrame=contributions.loc[contributions["author"]==name]
        files=contributions["fname"].unique()
        path_filter=set()
        if not author_doas.empty:
                files=author_doas.loc[author_doas["DOA"]>=doa]["fname"].unique()
        path_filter=set(files)
        branch=None
        caller=ctx.triggered_id
        if caller=="branch_picker":
            branch =None if not b or "all" == b else b         
        if caller=="tag_picker":
            branch=None if not t or "all" == t else t      
        tree = build_tree_structure(rp,branch if branch else "HEAD",path_filter)
        for p,o in tree.walk(files_only=True):
                if not p:
                        tree_dict[f"{o.name}"]=o.hash_string
                else:
                        tree_dict[f"{p}/{o.name}"]=o.hash_string
        df=tree.get_treemap()
        df=pd.DataFrame(df)
        fig=px.treemap(data_frame=df,parents=df["parent"],names=df["name"],ids=df["child"],color_discrete_map={'(?)':'lightgrey', 'file':'paleturquoise', 'folder':'crimson'},color=df["type"],custom_data=["id","type"],maxdepth=3,height=800)
        fig.update_layout(
        uniformtext=dict(minsize=10),
        margin = dict(t=50, l=25, r=25, b=25)
        )
        set_props("dir_info_loader",{"display":"auto"})
        return tree_dict,fig

@callback(
        Output("card-file-info","className"),
        Output("file-info","children"),
        Output("file-info-header","children"),
        Input("dir_treemap","clickData"),
        Input("branch_picker","value"),
        State("contribution_cache","data"),
        State("file-info-header","children"),
        prevent_initial_call=True
)
def populate_file_info(data,_,contributions,children):
        df=pd.DataFrame(contributions)
        file=data["points"][0]["id"]
        file_df:pd.DataFrame=df.loc[df["fname"]==file]
        top_3=file_df.sort_values(by="DOA",ascending=False).iloc[:3]
        if children==file:
                return "invisible",[],no_update
        div_children=[html.H4(f"Top {top_3['author'].size} module contributors")]
        for i,contr in enumerate(top_3.itertuples(name="Contr"),1):
                v=contr.DOA
                name=contr.author
                div_children.append(html.P(
                        f"{i}° {name} with normalized DOA {round(v,2)}"
                ))
        div = html.Div(children=div_children)

        return "visible",div,file

@callback(
        Output("author_picker","value"),
        Output("calculate_doa","n_clicks"),
        Input("reset_doa","n_clicks"),
        )
def reset_options(_):
        if _!=0:
                return None,0
@callback(
        Output("sidebar_info", "is_open"),
        Input("open_info", "n_clicks"),
        [State("sidebar_info", "is_open")],
)
def toggle_offcanvas(n1, is_open):
        if n1:
                return not is_open
        return is_open

@callback(
        Output("author_picker","options"),
        Input("authors_cache","data"),
)
def populate_author_picker(cache):
        authors_df=pd.DataFrame(cache)
        return authors_df["name"].unique().tolist()

@callback(
        Output("calculate_doa","disabled"),
        Input("author_picker","value"),
)
def populate_author_picker(auval):
        return auval==None