import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx,MATCH
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
from src.gui import AuthorDisplayerAIO,CustomTable,CommitDisplayerAIO
from datetime import datetime
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
        dbc.Row(id="repo_graph_row",children=[
                dbc.Col(
                        [       
                                dcc.Loading([
                                        dbc.Container(id="general_info"),
                                ])
                                
                        ]
                ,width=4,align="start"
                ),
                dbc.Col(
                        [
                                dcc.Loading([
                                        dbc.Container(id="truck_info"),
                                ])
                        ]
                ,width=4,align="start"
                ),
                dbc.Col(
                        [
                                
                        dbc.Container(id="contribution_info"),
                                
                        ]
                ,width=4,align="start"
                ),
                ]),
        dbc.Tabs([
                dbc.Tab(
                        [
                        dbc.Row(id="author_graph_row",children=[
                        dbc.Col(
                                [
                                        dcc.Loading(id="author_loader_graph",
                                        children=[dcc.Graph(id="graph",className="h-100")],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                ),
                                        html.Div([
                                                dcc.RadioItems(id="x_picker",options=[{"label":"Day of week","value":"dow"},{"label":"Per date","value":"date"}],value="dow",inline=True,labelClassName="px-2"),
                                                ]),
                                ],width=8,align="center"),
                        
                        dbc.Col([
                                dcc.Loading(id="author_overview_loader",children=[
                                                dcc.Graph(id="author_overview")
                                        ],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                        ),
                                ],width=4),
                        ],justify="center"),
                dbc.Row([
                        dbc.Col([
                                dcc.Loading(id="author_loader",children=[
                                        dcc.Graph(id="author_graph")
                                        ],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                        ),
                                dcc.Slider(id="date_slider",marks=None, tooltip={"placement": "bottom", "always_visible": False,"transform": "timestampToUTC"},),
                                ],width=12),
                ])
                ],label="General overview"
                ),
                dbc.Tab(label="Authors",children=[
                                        dbc.Row(children=[
                                                dbc.Col(width=12,align="center",id="authors_table"),
                                        ],justify="center"),]),
                dbc.Tab(label="Commits",children=[                                                  
                                        dbc.Row(children=[
                                                dbc.Col(width=12,align="center",id="commits_table"),
                                        ],justify="center"),
                                        ]),
                
                
                ]),
        # html.Div(id="test-div")
],fluid=True,className="p-10")
@callback(
        Output("general_info","children"),
        Input("branch_cache","data"),
        Input("authors_cache","data"),
        State("branch_picker","value"),
        State("repo_path","data"),
)
def populate_generale_info(cache,authors,branch,path,):
        if not cache:
                return no_update
        rp=RepoMiner(path)
        num_commits=len(cache)
        current_head=rp.repo.active_branch.name if not branch else branch
        num_authors=len(authors)
        current_commit=rp.get_commit(commit_hash=branch if branch else None)
        div=dbc.ListGroup(
                [
                        dbc.ListGroupItem([html.I(className="bi bi-graph-up pe-3 d-inline ms-2"),html.Span(f"Total number of commits: {num_commits}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-pen-fill d-inline ms-2 pe-3"),html.Span(f"Total number of authors: {num_authors}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-signpost-split-fill pe-3 d-inline ms-2"),html.Span(f"Current head of repository: {current_head}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-code-slash pe-3 d-inline ms-2"),html.Span([f"Last reachable commit: ",CommitDisplayerAIO(current_commit).create_comp()])])
                ]
        ,class_name=" py-3",flush=True)
        return html.Div([
                html.I(className="bi bi-git pe-3 d-inline h2"),html.Span("General overview",className="fw-bold h2"),html.Br(),
                div
        ])

@callback(
        Output("truck_info","children"),
        Input("truck_cache","data"),
        State("contribution_cache","data"),
)
def populate_truck_info(tf,contributions):
        sum_doa=0
        count=0
        for nm,c in contributions.items():
                for file,doa in c.items():
                        sum_doa+=doa
                        count+=1
        avg_doa=round(float(sum_doa/count),2)
        div=dbc.ListGroup(
                [       
                        dbc.ListGroupItem([html.Span("Calculated value: "+str(tf),className="ms-2"),html.Br(),]),
                        dbc.ListGroupItem([html.Span("Project's files' avarage DOA: "+str(avg_doa),className="ms-2"),html.Br(),]),
                        dbc.ListGroupItem([html.Span("Number of analyzed files: "+str(int(count/len(contributions.keys()))),className="ms-2"),html.Br(),])
                ]
        ,class_name=" py-3",flush=True)
        return html.Div([
                html.I(className="bi bi-truck pe-3 d-inline h2"),html.Span("Truck factor",className="fw-bold h2"),
                div
        ])
@callback(
        Output("commits_table","children"),
        Input("branch_cache","data")
)
def populate_commits_tab(data):
        data_to_show=list()
        for d in data:
                nd={
                        "Commit hash":CommitDisplayerAIO(CommitInfo(
                                d["commit_hash"],d["abbr_hash"],d["tree"],d["parent"],d["refs"],d["subject"],d["author_name"],d["author_email"],datetime.fromisoformat(d["date"]).date(),d["files"])).create_comp(),
                        "Full hash":d["commit_hash"],
                        "Author Name":d["author_name"],
                        "Date":datetime.fromisoformat(d["date"]).strftime(r"%d-%m-%Y"),
                }
                data_to_show.append(nd)
        return CustomTable(data_to_show,div_props={"fluid":True},filters={"Full hash":"equal","Author Name":"like"},sort={"Date":"date"}).create_comp()

@callback(
        Output("authors_table","children"),
        Input("contribution_cache","data"),
        Input("authors_cache","data")
)
def populate_authors_tab(contributions,data,doa_th=0.75):
        data_to_show=list()
        for d in data:
                author,cont=Author(d["email"],d["name"],d["commits_authored"]),[file for file, doa in contributions[f"{d['name']}|{d['email']}"].items() if doa >= doa_th]
                nd={
                        "Author":AuthorDisplayerAIO(author,cont).create_comp(),
                        "Email":d["email"],
                        "Files authored":len(cont)
                }
                data_to_show.append(nd)
        return CustomTable(data_to_show,filters={"Email":"like"},sort={"Files authored":"none"},div_props={"fluid":True}).create_comp()

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
        Output("contribution_info","children"),
        Input("contribution_cache","data"),
        State("authors_cache","data")
)
def populate_contributors(contributions,authors,th=0.75):
        contrs:dict[str,Iterable[str]]=dict()
        auth_df=pd.DataFrame(authors)
        
        for nm,c in contributions.items():
                contrs[nm]=list()
                for file,doa in c.items():
                        if doa >= th:
                                contrs[nm].append(file)
        contrs=sorted([(ne,files) for ne,files in contrs.items()] ,key=lambda t:len(t[1]),reverse=True)
        contrs=contrs[:3] if len(contrs)>=3 else contrs
        contributors=[html.I(className="bi bi-trophy-fill d-inline h3 pe-3"),
                html.H4(f"Your project's top {len(contrs)} contributors:",className="d-inline fw-bold")
        ]
        i=1
        list_items=[]
        for nm,c in contrs:
                name,email=nm.split("|")
                at=auth_df.loc[(auth_df["name"]==name) & (auth_df["email"]==email)]
                nd=AuthorDisplayerAIO(Author(at["email"].values[0],at["name"].values[0],at["commits_authored"].values[0]),c,text=f"<{at['email'].values[0]}>").create_comp()
                # nd=html.Div()
                cont_div=dbc.ListGroupItem([
                        nd
                ],className="py-1")
                i+=1
                list_items.append(cont_div)
        list_group = dbc.ListGroup(
        list_items,
        numbered=True,
        class_name=" py-3",flush=True
        )
        div = html.Div([*contributors,list_group])
        
        return div

@callback(
        Output("author_graph","figure"),
        Output("author_loader","display"),
        Input("branch_cache","data"),
        Input("date_slider","value"),
)
def populate_author_graph(data,value):
        if not value:
                return no_update,no_update
        df=pd.DataFrame(data)
        df["date"]=pd.to_datetime(df["date"])
        dt=unixToDatetime(value if isinstance(value,int) else value[0])
        # print(count_df["date"].tolist())
        df=df.loc[df["date"].dt.date <= dt.date()]
        count_df=df.groupby(["author_name"]).size().reset_index(name="commit_count")
        fig=px.bar(count_df,x="commit_count",y="author_name",labels=common_labels,title="Authors effort over time",color="author_name")
        return fig,"auto"

@callback(
        Output("date_slider","min"),
        Output("date_slider","max"),
        Output("date_slider","value"),
        Output("date_slider","marks"),
        Input("branch_cache","data"),
)
def adjust_date_slider(data):
        df=pd.DataFrame(data)
        df["date"]=pd.to_datetime(df["date"])
        min_date=df["date"].min()
        max_date=df["date"].max()
        min=unixTimeMillis(min_date)#the first date
        max=unixTimeMillis(max_date)#the last date
        value=int(max-(max-min)/2)#default: the first
        marks=getMaxMinMarks(min_date,max_date)
        return min,max,value,marks