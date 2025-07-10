from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update,State,set_props,ctx
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor
from repository_miner import RepoMiner
from src.utility import get_dataframe
from src.app.helper import retrieve_contribution_data,parallel_commit_retrievial
import pandas as pd
import dash_bootstrap_components as dbc
import re
from functools import partial
from logging import getLogger
logger=getLogger()

assets_folder=Path(__file__).parent.parent.joinpath("gui","assets")
def start_app(repo_path:Union[str|Path],cicd_test:bool,env:bool):
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    # print(path)
    pr_name=re.subn(r"_|-"," ",Path(path).name)[0].capitalize()
    app=Dash(name=__name__,title="PVT",assets_folder=assets_folder.as_posix(),external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.BOOTSTRAP,assets_folder.joinpath("css").as_posix()],use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix())
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Directory analysis", href="/dir")),
            dbc.Button(id="reload_button",children=[html.I(className="bi bi-arrow-counterclockwise p-1")],className="p1 bg-transparent border-0",value=0),
            dbc.Button(id="open_info",children=[html.I(className="bi bi-list p-1")],className="p1 bg-transparent border-0"),
        ],
        brand=pr_name,
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-2",
        sticky=True,
        fluid=True
    )
    logger.info("Loading necessary info, hang tight")
    contributions,tr_fa=retrieve_contribution_data(path)
    logger.info("You're good to go")
    general_options=dbc.Offcanvas(id="sidebar_info",title="History filters",is_open=False,children=
        [dbc.Stack(
        [
            dbc.RadioItems(id="filter_picker",options=[{"label":"Branch picker","value":"branch_option"},{"label":"Tag picker","value":"tag_option"}],value="branch_option",inline=True,switch=True),
            html.Div([dbc.Label(["Branch Picker"]),dcc.Dropdown(id="branch_picker",searchable=True,clearable=True,placeholder="Branch name")],id="branch_picker_div",className="d-inline"),
            html.Div([dbc.Label(["Tag Picker"]),dcc.Dropdown(id="tag_picker",searchable=True,clearable=True,placeholder="Tag name")],id="tag_picker_div",className="d-inline"),
        ], gap=2,className="p-2")
        ])
    app.layout = html.Div([
        dcc.Store(id="contribution_cache",data=contributions.to_dict("records"),storage_type="session"),
        dcc.Store(id="truck_cache",data=tr_fa,storage_type="session"),
        dcc.Loading(children=[
            dcc.Store(id="branch_cache"),
            dcc.Store(id="commit_df_cache",storage_type="memory"),
            ],fullscreen=True),
        dcc.Store(id="authors_cache"),
        dcc.Store("repo_path",data=path,storage_type="session"),
        navbar,
        general_options,
        dbc.Tooltip("Open filter pickers",target="open_info"),
        dbc.Row([ 
                dbc.Col(
                        children=[
                            dbc.Container([
                            ],fluid=True),
                            page_container
                            ],
                        width=12,align="end"), 
            ],align="start")        
    ])
    
    if not cicd_test:
        if env=="DEV":
            app.run(debug=True,dev_tools_hot_reload=True)
        else:
            open("http://localhost:8080/")
            serve(app.server,host="localhost",port=8080,_quiet=True,threads=100)

@callback(
        Output("commit_df_cache","data"),
        Input("reload_button","n_clicks"),
        State("repo_path","data")
)
def listen_data(_,data):
        rp=RepoMiner(data)
        set_props("branch_picker",{"options":list(( b.name for b in rp.local_branches()))})
        set_props("tag_picker",{"options":list(( b.name for b in rp.get_tags()))})
        commits=parallel_commit_retrievial(rp)
        commit_df=pd.DataFrame(map(lambda c:c.__dict__,commits))
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
        Output("branch_cache","data"),
        Input("branch_picker","value"),
        Input("tag_picker","value"),
        Input("commit_df_cache","data"),
        State("repo_path","data"),
)
def filter_branch_data(v,t,cache,path):
        caller=ctx.triggered_id
        branch=None
        if caller=="branch_picker" and not (not  v or "all" == v ):
            branch = v
        if caller=="tag_picker" and not ( not t or "all" == t):
            branch= t
        if branch:
            df=pd.DataFrame(cache)
            rp=RepoMiner(path)
            b=[c.commit_hash for c in rp.get_branch(branch).traverse_commits()] if caller=="branch_picker" else [c.commit_hash for c in rp.get_tag(branch).traverse_commits()]
            df=df[df["commit_hash"].isin(b)]
            cache = df.to_dict("records")
        cache = cache if cache else no_update
        return cache

@callback(
        Output("branch_picker","disabled"),
        Output("tag_picker","disabled"),
        Output("branch_picker","value"),
        Output("tag_picker","value"),
        Input("filter_picker","value"),
)
def choose_filter(choice):
        output=[False,True,None,None] if choice == "branch_option" else [True,False,None,None]
        return output