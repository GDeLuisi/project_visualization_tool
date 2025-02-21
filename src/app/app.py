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
def start_app(repo_path:Union[str|Path],cicd_test:bool):
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    print(path)
    app=Dash(name="Project Visualization Tool",title="PVT",external_stylesheets=[dbc.themes.BOOTSTRAP],use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix())
    app.layout = html.Div([
        dcc.Store(id="commit_df"),
        dcc.Store(id="author_df"),
        dcc.Store("repo_path",data=path),
        page_container
    ])
    if not cicd_test:
        open("http://localhost:8050/")
        serve(app.server,host="localhost",port=8050)
    # app.run(debug=True,dev_tools_hot_reload=True)
