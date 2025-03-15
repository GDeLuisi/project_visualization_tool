import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx
from src._internal import RepoMiner,make_commit_dataframe,prune_common_commits,getMaxMinMarks,unixTimeMillis,unixToDatetime
from typing import Iterable
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
truck_facto_modal=dbc.Modal(
        [
                dbc.ModalHeader("How we calculate the truck factor"),
                dbc.ModalBody("The truck factor is calculated through a naive version of the AVL algorithm for truck factor calculation; the DOA (Degree of Authorship) used for truck factor calculation is obtained evaluating the number of non-whitespace commits authored by each author (it will not take into account the number of lines changed) for each file of the project. The final number it is the result of an operation of thresholding for which we discard all DOA normalized values inferior to 0.75, the resulting DOAs obtained from the filtering process are then used to estabilish the number of file authored by each author in order to lazily remove each author from the calculation until at least 50% of project's file are 'orphans'(no file author alive). The number of author to remove in order to satisfy the previous condition is the effective truck factor calculated for the project" ),
        ],"truck_factor_modal",is_open=False
)
layout = dbc.Container([
        truck_facto_modal,
        html.H1("General Overview"),
        html.Br(),
        dbc.Row(id="repo_graph_row",children=[
                dbc.Col(
                        [
                                html.Div([
                                        dbc.Label(["Display mode picker"],html_for="x_picker",check=True),
                                        dcc.RadioItems(id="x_picker",options=[{"label":"Day of week","value":"dow"},{"label":"Per date","value":"date"}],value="dow",inline=True,labelClassName="px-2"),
                                        ]),
                                dcc.Loading(id="author_loader_graph",
                                children=[dcc.Graph(id="graph",className="h-100")],
                                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                        ),
                        ],width=8,align="end"),
                dbc.Col(
                        [       
                                dcc.Loading(id="truck_factor_loader",
                                children=[
                                                dbc.Card([
                                                        dbc.CardHeader(id="truck_factor_header"),
                                                        dbc.CardBody(id="truck_factor"),
                                                        dbc.CardFooter([dbc.Button(["More info"],id="truck_factor_info")])
                                                ])
                                        ],
                                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                        ),
                        ],width=4,align="center"),
                ],justify="center"),
        dbc.Row(id="author_graph_row",children=[

                dbc.Col([
                        dcc.Loading(id="author_loader",children=[
                                dcc.Graph(id="author_graph")
                                ],
                                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                ),
                        dcc.Slider(id="date_slider",marks=None, tooltip={"placement": "bottom", "always_visible": True,"transform": "timestampToUTC"},),
                        ],width=8),
                dbc.Col([
                        dcc.Loading(id="author_overview_loader",children=[
                                        dcc.Graph(id="author_overview")
                                ],
                                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                ),
                        ],width=4),
                ]),
        # html.Div(id="test-div")
],fluid=True,className="p-10")
@callback(
        Output("truck_factor_modal","is_open"),
        Input("truck_factor_info","n_clicks"),
        prevent_initial_call=True
)
def open_truck_modal(_):
        if _==0:
                return no_update
        return True
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
        Output("author_overview","figure"),
        Input("authors_cache","data"),
)
def update_pie_graph(data):
        df=pd.DataFrame(data)
        df["contributions"]=df["commits_authored"].apply(lambda r: len(r))
        df=df.groupby("name",as_index=False).sum(True)
        # print(df.head())
        tot:int=df["contributions"].sum()
        th_percentage=5*tot/100
        df.loc[df['contributions'] < th_percentage, 'name'] = 'Minor contributors total effort'
        # print(df.head())
        fig = px.pie(df, values='contributions', names='name', title='Authors contribution to the project')
        return fig

@callback(
        Output("truck_factor_header","children"),
        Output("truck_factor","children"),
        Input("truck_cache","data"),
        State("repo_path","data"),
        State("contribution_cache","data")
)
def populate_truck_factor(tf,pr,contributions):
        pr_name=Path(pr).name
        contrs:dict[str,Iterable[str]]=dict()
        th=0.75
        for nm,c in contributions.items():
                contrs[nm]=list()
                for file,doa in c.items():
                        if doa >= th:
                                contrs[nm].append(file)
        contrs=sorted([(ne,files) for ne,files in contrs.items()] ,key=lambda t:len(t[1]),reverse=True)
        contrs=contrs[:3] if len(contrs)>=3 else contrs
        contributors=[
                html.H3(f"The project's truck factor amounts at {tf}"),
                html.Br(),
                html.H4(f"Your project's top {len(contrs)} contributors:")
        ]
        for nm,c in contrs:
                name,email=nm.split("|")
                contributors.append(html.P(f"Author {name} <{email}> with {len(c)} files authored"))
        div = html.Div(contributors)
        
        return html.H2(f"Truck factor for project {pr_name}"),div

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
