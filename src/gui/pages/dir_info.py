import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx,ALL,MATCH
from src._internal import RepoMiner,make_commit_dataframe,prune_common_commits,getMaxMinMarks,unixTimeMillis,unixToDatetime
import dash.html as html
from datetime import date
import plotly.express as px
import pandas as pd
from pathlib import Path
from src._internal.data_typing import Author,CommitInfo,TreeStructure,File,Folder
import dash_bootstrap_components as dbc
from io import StringIO
import json
import time
from typing import Union
from src._internal import find_satd
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
                                                children=[html.Div([dbc.Label(["Author Email Picker"]),dcc.Dropdown(id="author_picker_email",searchable=True,disabled=True,clearable=True,placeholder="Author email")]),],
                                                width=12)
                                        
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
        dcc.Store("satd_files_cache"),
        dcc.Loading(id="dir_info_loader",display="show",fullscreen=True),
        dbc.Row([
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
        Output("satd_files_cache","data"),
        Output("satd_pagination","max_value"),
        Input("file_info_cache","data"),
        State("repo_path","data"),
)
def find_satd_files(cache:dict[str,str],path):
        rp=RepoMiner(path)
        satd_list_dict=list()
        for p,o in cache.items():
                # print(p)
                satds:dict[int,str]=find_satd(rp.get_source(o),Path(p).suffix)
                if len(satds)>0:
                        satd_list_dict.append((p,satds))
        return satd_list_dict,ceil(len(satd_list_dict)/items_per_page)

@callback(
        Output("satd_files","children"),
        Input("satd_pagination","active_page"),
        Input("satd_files_cache","data")
)
def populate_satd_list(page,cache):
        if not cache:
                return no_update
        buttons:list[dbc.ListGroupItem]=list()
        start_value=(page-1)*items_per_page
        to_add=cache[start_value:start_value+items_per_page]
        for p,satds in to_add:
                buttons.append(dbc.ListGroupItem(SATDDisplayerAIO(p,satds,span_props=dict(className="fw-bold ",style={"cursor":"pointer"}),modal_props={"scrollable":True}).create_comp()))
        return buttons

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
        tree_dict:dict[str,str]=dict()
        if name and email:
                author=f"{name}|{email}"
                author_doas=cache[author]
        tree = rp.get_dir_structure(b)
        for p,o in tree.walk(files_only=True):
                tree_dict[f"{p}/{o.name}"]=o.hash_string
        # print(tree_dict)
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
        fig=px.treemap(data_frame=df,parents=df["parent"],names=df["name"],ids=df["child"],color_discrete_map={'(?)':'lightgrey', 'file':'paleturquoise', 'folder':'crimson'},color=df["type"],custom_data=["id","type"],maxdepth=3,height=800)
        fig.update_layout(
        uniformtext=dict(minsize=10),
        margin = dict(t=50, l=25, r=25, b=25)
        )
        set_props("dir_info_loader",{"display":"auto"})
        # fig=px.treemap(parents = ["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve","Noam"],names = ["Eve","Cain", "Seth", "Enos/Noam", "Noam", "Abel", "Awan", "Enoch", "Azura","Aqua"],)
        return tree_dict,fig

@callback(
        Output("card-file-info","className"),
        Output("file-info","children"),
        Output("file_cache","data"),
        Output("file-info-header","children"),
        Input("dir_treemap","clickData"),
        Input("branch_picker","value"),
        State("repo_path","data"),
        State("file_cache","data"),
        State("file-info-header","children"),
)
def populate_file_info(data,_,path,cache,children):
        if not data:
                return no_update,no_update,no_update,no_update
        file=data["points"][0]["id"]
        # print(data)
        if children==file:
                return "invisible",[],no_update,""
        if file in cache:
                doas=cache[file]
        else:
                rp=RepoMiner(path)
                doas=rp.calculate_DOA(file)
                nd:dict[str,float]=dict()
                for k,v in doas.items():
                        nd[f"{k.name}|{k.email}"]=v
                cache[file]=nd
                doas=nd
        ordered_doas=sorted(((k,round(v,2)) for k,v in doas.items()),reverse=True,key=lambda item:item[1])[:3]
        
        div_children=[html.H4(f"Top 3 module contributors")]
        for i,(k,v) in enumerate(ordered_doas,1):
                name,email=k.split('|')
                div_children.append(html.P(
                        f"{i}° {name} <{email}> with normalized DOA {v}"
                ))
        div = html.Div(children=div_children)

        return "visible",div,cache,file

@callback(
        Output("author_picker","value"),
        Output("author_picker_email","value"),
        Output("calculate_doa","n_clicks"),
        Input("reset_doa","n_clicks"),
        )
def reset_options(_):
        if _!=0:
                return None,None,0
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

#FIXME button stays active if one of the two dropdowns is cleared after selection
@callback(
        Output("calculate_doa","disabled"),
        Input("author_picker_email","value"),
        Input("author_picker","value"),
)
def populate_author_picker(val,auval):
        return val==None or auval==None