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
dash.register_page(__name__,"/")
common_labels={"date":"Date","commit_count":"Number of commits","author_email":"Author's email","author_name":"Author's name","dow":"Day of the week"}

layout = dbc.Container([
        dbc.Row(id="choices",children=[
                dbc.Col(
                        children=[dbc.Label(["Display mode picker"]),dcc.Dropdown(id="x_picker",value="dow",options=[{"label":"Day of week","value":"dow"},{"label":"Per date","value":"date"}]),],
                        width=5),
                ],align="center",justify="evenly"),
        dbc.Row(id="repo_graph_row",children=[
                dcc.Loading(id="author_loader_graph",
                        children=[dcc.Graph(id="graph")],
                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                        ),
                ]),
        html.Br(),
        dbc.Row(id="author_graph_row",children=[
                
                dcc.Loading(id="author_loader",children=[
                        dcc.Graph(id="author_graph")
                        ],
                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                ),
                ]),
        dbc.Row([
                dcc.Slider(id="date_slider",marks=None, tooltip={"placement": "bottom", "always_visible": True,"transform": "timestampToUTC"},),
                ]),
        # html.Div(id="test-div")
])

@callback(
        Output("graph","figure"),
        Input("x_picker","value"),
        Input("branch_cache","data"),
        State("branch_picker","value"),
)
def update_count_graph(pick,data,branch):
        commit_df=pd.DataFrame(data)
        if pick =="dow":
                count_df=commit_df.groupby(["dow","dow_n"])
                count_df=count_df.size().reset_index(name="commit_count")
                count_df.sort_values("dow_n",ascending=True,inplace=True)
                fig=px.bar(count_df,x=pick,y="commit_count",labels=common_labels,title=f"Commit Distribution {branch if branch else ''}")
        else:
                count_df=commit_df.groupby(["date"]).size().reset_index(name="commit_count")
                fig=px.area(count_df,hover_data=["date"],x=pick,y="commit_count",labels=common_labels,title=f"Commit Distribution {branch if branch else ''}")        
        return fig


@callback(
        Output("author_graph","figure"),
        Output("author_loader","display"),
        Output("date_slider","min"),
        Output("date_slider","max"),
        Output("date_slider","value"),
        Output("date_slider","marks"),
        Input("branch_cache","data"),
        Input("date_slider","value"),

)
def populate_author_graph(data,value):
        df=pd.DataFrame(data)
        df["date"]=pd.to_datetime(df["date"])
        triggerer=ctx.triggered_id
        if triggerer!= "date_slider":
                min_date=df["date"].min()
                max_date=df["date"].max()
                min=unixTimeMillis(min_date)#the first date
                max=unixTimeMillis(max_date)#the last date
                value=int(max-(max-min)/2)#default: the first
                marks=getMaxMinMarks(min_date,max_date)
                dt=unixToDatetime(value if isinstance(value,int) else value[0])
                # print(count_df["date"].tolist())
                df=df.loc[df["date"].dt.date <= dt.date()]
                count_df=df.groupby(["author_name"]).size().reset_index(name="commit_count")
                fig=px.bar(count_df,x="commit_count",y="author_name",labels=common_labels,title="Author commits effort",color="author_name")
                return fig,"auto",min,max,value,marks
        dt=unixToDatetime(value if isinstance(value,int) else value[0])
        # print(count_df["date"].tolist())
        df=df.loc[df["date"].dt.date <= dt.date()]
        count_df=df.groupby(["author_name"]).size().reset_index(name="commit_count")
        fig=px.bar(count_df,x="commit_count",y="author_name",labels=common_labels,title="Author commits effort",color="author_name")
        return fig,"auto",no_update,no_update,no_update,no_update
        