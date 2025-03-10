from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update,DiskcacheManager,State,set_props
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve
from concurrent.futures import ThreadPoolExecutor
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
            dbc.Button(id="open_info",children=[html.I(className="bi bi-list p-1")],className="p1 bg-transparent border-0"),
        ],
        brand="Project Visualization Tool",
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-2",
        sticky=True,
        fluid=True
    )
    
    general_options=dbc.Offcanvas(id="sidebar_info",title="Directory discovery",is_open=False,children=
        [dbc.Stack(
        [
            html.Div([dbc.Label(["Branch Picker"]),dcc.Dropdown(id="branch_picker",searchable=True,clearable=True,placeholder="Branch name")]),
        ], gap=2,className="p-2")
        ])
    app.layout = html.Div([
        dcc.Store(id="contribution_cache"),
        dcc.Store(id="truck_cache"),
        dcc.Store(id="branch_cache"),
        dcc.Store(id="authors_cache"),
        dcc.Store("repo_path",data=path,storage_type="session"),
        navbar,
        general_options,
        dbc.Row([ 
                dbc.Col(
                        children=[
                            dbc.Container([
                            dcc.Loading(fullscreen=True,children=[
                                dcc.Store(id="commit_df_cache",storage_type="session"),
                                
                                ]),
                            page_container
                            ],fluid=True)
                            ],
                        width=12,align="end"), 
            ],align="start")        
    ])
    if not cicd_test:
        if env=="DEV":
            app.run(debug=True,dev_tools_hot_reload=True)
        else:
            open("http://localhost:8050/")
            serve(app.server,host="localhost",port=8050,_quiet=True)

@callback(
        Output("commit_df_cache","data"),
        Output("truck_cache","data"),
        Output("contribution_cache","data"),
        Output("authors_cache","data"),
        Input("reload_button","n_clicks"),
        State("repo_path","data"),
        State("commit_df_cache","data"),
)
def listen_data(_,data,cache):
        if cache and _==0:
            return no_update,no_update,no_update,no_update
        rp=RepoMiner(data)
        with ThreadPoolExecutor() as executor:
            result=executor.submit(rp.get_truck_factor)
        set_props("branch_picker",{"options":list(( b.name for b in rp.get_branches(deep=False)))})
        # set_props("author_loader",{"display":"show"})
        # set_props("author_loader_graph",{"display":"show"})
        m_count=None
        commit_df=pd.DataFrame()
        authors=pd.DataFrame()
        for commit_list in rp.lazy_load_commits(max_count=m_count):
                cl_df=pd.concat(map(lambda c:c.get_dataframe(),commit_list))
                # print(cl_df.info())
                commit_df=pd.concat([commit_df,cl_df])
        commit_df.reset_index(inplace=True)
        commit_df["date"]=pd.to_datetime(commit_df["date"])
        commit_df["dow"]=commit_df["date"].dt.day_name()
        commit_df["dow_n"]=commit_df["date"].dt.day_of_week
        for author in rp.get_authors():
            authors=pd.concat([authors,author.get_dataframe()])
        # set_props("author_loader_graph",{"display":"auto"})
        # set_props("author_loader",{"display":"auto"})
        tr_fa,contributions=result.result()
        contributions=dict([(f"{a.name}{a.email}",c) for a,c in contributions.items()])
        return commit_df.to_dict("records"),tr_fa,contributions,authors.to_dict("records")

@callback(
        Output("branch_cache","data"),
        Input("branch_picker","value"),
        Input("commit_df_cache","data"),
        State("repo_path","data"),
        prevent_initial_call=True
)
def filter_branch_data(v,cache,path):
        branch=None if not v or "all" == v else v            
        if v  and v!="all":
            df=pd.DataFrame(cache)
            rp=RepoMiner(path)
            b=rp.get_branch(branch)
            df=df[df["commit_hash"].isin(b.commits)] if v else df
            return df.to_dict("records")
        return cache

    
# @callback(
#     Output("test-div","children"),
#     Input("truck_cache","data"),
#     Input("contribution_cache","data"),
# )
# def test(tf,cont):
#     return [tf,html.Div([json.dumps(cont)])]