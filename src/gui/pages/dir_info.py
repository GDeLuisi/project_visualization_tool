import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx
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
from logging import getLogger
logger=getLogger("mainpage")
dash.register_page(__name__,"/dir")


layout = dbc.Container([
        dbc.Row([
                dcc.Loading(id="author_loader_graph",
                        children=[dcc.Graph("dir_treemap")],
                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                        ),
                ]),
                ]),

@callback(
        Output("dir_treemap","figure"),
        Input("repo_path","data")
)
def populate_treemap(data):
        # df=pd.DataFrame(cache)
        rp=RepoMiner(data)
        tree = rp.get_dir_structure()
        df=tree.get_treemap()
        fig=px.treemap(parents=df["parent"],names=df["name"],ids=df["child"],color_discrete_map={'(?)':'lightgrey', 'file':'gold', 'folder':'darkblue'},color=df["type"])
        
        # fig=px.treemap(parents = ["", "Eve", "Eve", "Seth", "Seth", "Eve", "Eve", "Awan", "Eve","Noam"],names = ["Eve","Cain", "Seth", "Enos/Noam", "Noam", "Abel", "Awan", "Enoch", "Azura","Aqua"],)
        return fig