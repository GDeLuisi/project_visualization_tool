from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update,State,set_props
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve,server
from concurrent.futures import ProcessPoolExecutor
from repository_miner import RepoMiner
from src.utility import get_dataframe
import truck_factor_gdeluisi.main as tf_calculator
import pandas as pd
import dash_bootstrap_components as dbc
import re
from logging import getLogger
logger=getLogger()

assets_folder=Path(__file__).parent.parent.joinpath("gui","assets")
def start_app(repo_path:Union[str|Path],cicd_test:bool,env:bool):
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    # print(path)
    pr_name=re.subn(r"_|-"," ",Path(path).name)[0].capitalize()
    app=Dash(name=pr_name,title="PVT",assets_folder=assets_folder.as_posix(),external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP,assets_folder.joinpath("css").as_posix()],use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix())
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Directory analysis", href="/dir")),
            dbc.Button(id="reload_button",children=[html.I(className="bi bi-arrow-counterclockwise p-1")],className="p1 bg-transparent border-0",value=0),
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
        dcc.Loading(children=[
            dcc.Store(id="truck_cache"),
            ],fullscreen=True),
        dcc.Store(id="branch_cache"),
        dcc.Store(id="authors_cache"),
        dcc.Store("repo_path",data=path,storage_type="session"),
        navbar,
        general_options,
        
        dbc.Row([ 
                dbc.Col(
                        children=[
                            dbc.Container([
                            dcc.Store(id="commit_df_cache",storage_type="memory"),
                            ],fluid=True),
                            page_container
                            ],
                        width=12,align="end"), 
            ],align="start")        
    ])
    logger.info("Loading necessary info, hang tight")
    if not cicd_test:
        if env=="DEV":
            app.run(debug=True,dev_tools_hot_reload=True)
        else:
            open("http://localhost:8050/")
            serve(app.server,host="localhost",port=8050,_quiet=True,threads=100)

@callback(
        Output("commit_df_cache","data"),
        Input("reload_button","n_clicks"),
        State("repo_path","data"),
        State("commit_df_cache","data"),
)
def listen_data(_,data,cache):
        commit_df=pd.DataFrame(cache)
        rp=RepoMiner(data)
        set_props("branch_picker",{"options":list(( b.name for b in rp.local_branches()))})
        commits=list(rp.retrieve_commits(merges=True))
        cl_df=pd.concat(map(lambda c:get_dataframe(c),commits))
        commit_df=pd.concat([commit_df,cl_df])
        commit_df.reset_index(inplace=True,drop=True)
        commit_df["date"]=pd.to_datetime(commit_df["date"])
        commit_df["dow"]=commit_df["date"].dt.day_name()
        commit_df["dow_n"]=commit_df["date"].dt.day_of_week
        commit_df=commit_df.drop("tree_func",axis=1)
        return commit_df.to_dict("records")
        
@callback(
    Output("authors_cache","data"),
    Input("reload_button","n_clicks"),
    State("repo_path","data"),
)
def load_authors(_,data):
    rp=RepoMiner(data)
    authors=pd.DataFrame()
    for author in rp.authors():
        authors=pd.concat([authors,get_dataframe(author)])
    return authors.to_dict("records")

@callback(
    Output("truck_cache","data"),
    Output("contribution_cache","data"),
    Input("reload_button","n_clicks"),
    State("repo_path","data"),
)
def load_truck_info(_,data):
    contributions=tf_calculator.compute_DOA(tf_calculator.create_contribution_dataframe(data,only_of_files=False))
    tf_contributions=tf_calculator.filter_files_of_interest(contributions)
    tr_fa=tf_calculator.compute_truck_factor_from_contributions(tf_contributions)
    return tr_fa,contributions.to_dict("records")

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
            b=rp.retrieve_commits(branch)
            df=df[df["commit_hash"].isin(b.commits)] if v else df
            return df.to_dict("records")
        return cache if cache else no_update
    