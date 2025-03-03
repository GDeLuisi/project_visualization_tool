from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update,DiskcacheManager
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve
from src._internal import RepoMiner
from time import strptime,strftime
import pandas as pd
import numpy as np
import plotly.express as px
from src._internal import make_commit_dataframe,make_author_dataframe
from src.utility.logs import setup_logging
import dash_bootstrap_components as dbc
def start_app(repo_path:Union[str|Path],cicd_test:bool,env:bool):
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    # print(path)
    app=Dash(name="Project Visualization Tool",title="PVT",assets_folder=Path(__file__).parent.parent.joinpath("gui","assets").as_posix(),external_stylesheets=[dbc.themes.BOOTSTRAP],use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix())
    navbar = dbc.NavbarSimple(
        children=[
            dbc.NavItem(dbc.NavLink("Home", href="/")),
            dbc.NavItem(dbc.NavLink("Directory analysis", href="/dir")),
        ],
        brand="Project Visualization Tool",
        brand_href="/",
        color="dark",
        dark=True,
        className="mb-2",
    )
    app.layout = html.Div([
        navbar,
        dbc.Container([
            dcc.Store(id="commit_df"),
            dcc.Store(id="author_df"),
            dcc.Store("repo_path",data=path,storage_type="session"),
            dbc.Row([dbc.Col(
                        children=[dbc.Label(["Branch Picker"]),dcc.Dropdown(id="branch_picker",searchable=True,clearable=True,placeholder="Branch name")],
                        width=5),],align="center"),
            page_container
        ],fluid=True)
    ])
    if not cicd_test:
        if env=="DEV":
            app.run(debug=True,dev_tools_hot_reload=True)
        else:
            open("http://localhost:8050/")
            serve(app.server,host="localhost",port=8050,_quiet=True)
