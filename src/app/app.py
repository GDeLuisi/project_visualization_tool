from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update,DiskcacheManager,State,set_props
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve
from src._internal import RepoMiner
from time import strptime,strftime
import json
import pandas as pd
import numpy as np
import plotly.express as px
from src.utility.logs import setup_logging
import dash_bootstrap_components as dbc
def start_app(repo_path:Union[str|Path],cicd_test:bool,env:bool):
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    # print(path)
    app=Dash(name="Project Visualization Tool",title="PVT",assets_folder=Path(__file__).parent.parent.joinpath("gui","assets").as_posix(),external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP],use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix())
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Directory analysis", href="/dir")),
            dbc.Button(id="reload_button",children=[html.I(className="bi bi-arrow-counterclockwise p-1")],className="p1 bg-transparent border-0"),
        ],
        brand="Project Visualization Tool",
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-2",
        sticky=True,
        fluid=True
    )
    sidebar_stack=dbc.Stack(
        [
            html.Div([dbc.Label(["Branch Picker"]),dcc.Dropdown(id="branch_picker",searchable=True,clearable=True,placeholder="Branch name")]),
            html.Div([dbc.Label(["Author Picker"]),dcc.Dropdown(id="author_picker",searchable=True,clearable=True,placeholder="Author name")]),
        ], gap=2,className="p-2"
    )
    app.layout = html.Div([
        navbar,
        dbc.Container([
            # dcc.Store(id="commit_df"),
            # dcc.Store(id="author_df"),
            dcc.Store(id="contribution_cache"),
            dcc.Store(id="truck_cache"),
            dcc.Store(id="branch_cache"),
            dcc.Store("repo_path",data=path,storage_type="session"),
            dcc.Loading(fullscreen=True,children=[
                dcc.Store(id="commit_df_cache",storage_type="session"),
                ]),
            dbc.Row([
                dbc.Col(
                        children=[sidebar_stack],
                        width=2,align="start"), 
                dbc.Col(
                        children=[page_container],
                        width=10,align="end"), 
            ],align="start"),
            html.Div(id="test-div")
            
        ],fluid=True)
    ])
    if not cicd_test:
        if env=="DEV":
            app.run(debug=True,dev_tools_hot_reload=True)
        else:
            open("http://localhost:8050/")
            serve(app.server,host="localhost",port=8050,_quiet=True)

@callback(
        Output("commit_df_cache","data"),
        Input("reload_button","n_clicks"),
        State("repo_path","data"),
        State("commit_df_cache","data"),
)
def listen_data(_,data,cache):
        if cache and _==0:
            return cache
        rp=RepoMiner(data)
        set_props("branch_picker",{"options":list(( b.name for b in rp.get_branches(deep=False)))})
        # set_props("author_loader",{"display":"show"})
        # set_props("author_loader_graph",{"display":"show"})
        m_count=None
        commit_df=pd.DataFrame()
        for commit_list in rp.lazy_load_commits(max_count=m_count):
                cl_df=pd.concat(map(lambda c:c.get_dataframe(),commit_list))
                # print(cl_df.info())
                commit_df=pd.concat([commit_df,cl_df])
        commit_df.reset_index(inplace=True)
        commit_df["date"]=pd.to_datetime(commit_df["date"])
        commit_df["dow"]=commit_df["date"].dt.day_name()
        commit_df["dow_n"]=commit_df["date"].dt.day_of_week
        authors=commit_df["author_name"].unique().tolist()
        set_props("author_picker",{"options":authors})
        # set_props("author_loader_graph",{"display":"auto"})
        # set_props("author_loader",{"display":"auto"})
        
        return commit_df.to_dict("records")
@callback(        
        Output("truck_cache","data"),
        Output("contribution_cache","data"),
        Input("commit_df_cache","data"),
        State("repo_path","data"),
        State("truck_cache","data"),
        State("contribution_cache","data"),
        prevent_initial_call=True
        )
def calculate_truck_factor(_,path,tf,cnt):
    rp=RepoMiner(path)
    tr_fa,contributions=rp.get_truck_factor()
    contributions=[dict(contribution=c,author=a.JSON_serialize()) for a,c in contributions.items()]
    # print(tr_fa,contributions)
    return tr_fa,contributions
@callback(
        Output("branch_cache","data"),
        Input("branch_picker","value"),
        Input("author_picker","value"),
        Input("commit_df_cache","data"),
        State("repo_path","data"),
        prevent_initial_call=True
)
def filter_branch_data(v,author,cache,path):
        branch=None if not v or "all" == v else v            
        if v or author and v!="all":
            df=pd.DataFrame(cache)
            if v:
                rp=RepoMiner(path)
                b=rp.get_branch(branch)
                df=df[df["commit_hash"].isin(b.commits)] if v else df
            df=df[df["author_name"]==author] if author else df
            # df.info()
            return df.to_dict("records")
        return cache
    
@callback(
    Output("test-div","children"),
    Input("truck_cache","data"),
    Input("contribution_cache","data"),
)
def test(tf,cont):
    return [tf,html.Div([json.dumps(cont)])]