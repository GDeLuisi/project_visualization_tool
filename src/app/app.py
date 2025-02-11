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

def start_app(repo_path:Union[str|Path]):
    import diskcache
    cache = diskcache.Cache("./cache")
    background_callback_manager = DiskcacheManager(cache)
    path=repo_path if isinstance(repo_path,str) else repo_path.as_posix()
    print(path)
    app=Dash(name="Project Visualization Tool",title="PVT",background_callback_manager=background_callback_manager,use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix(),assets_folder=Path(__file__).parent.parent.joinpath("gui","assets").as_posix())
    app.layout = html.Div([
        dcc.Store(id="commit_df"),
        dcc.Store(id="author_df"),
        dcc.Store("repo_path",data=path),
        page_container
    ])
    # open("http://localhost:8050/")
    # serve(app.server,host="localhost",port=8050)
