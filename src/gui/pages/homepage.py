import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx,MATCH
from dash.exceptions import PreventUpdate
from typing import Iterable
import dash.html as html
from datetime import date
import plotly.express as px
import pandas as pd
from pathlib import Path
from repository_miner import RepoMiner
from repository_miner.data_typing import CommitInfo
from src._internal.data_typing import Author,TreeStructure,File,Folder
import dash_bootstrap_components as dbc
from io import StringIO
from dash_ag_grid import AgGrid
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

column_defs_commits=[
                {"field": "commit_hash", 'headerName': 'Commit Hash',"filter": "agTextColumnFilter"},
                {"field": "author_name",'headerName': 'Author Name',"filter": "agTextColumnFilter"},
                {
                        "field":"date",
                        "headerName":"Date",
                        "headerName": "Date",
                        "filter": "agDateColumnFilter",
                        "sortable":True,
                        # "valueGetter": {"function": "d3.timeParse('%d-%m-%Y')(params.data.date)"},
                        # "valueFormatter": {"function": "params.data.date"}
                }
        ]

column_defs_authors=[
        {"field": "email", 'headerName': 'Author Email',"filter": "agTextColumnFilter"},
        {"field": "name",'headerName': 'Author Name',"filter": "agTextColumnFilter"},
        {"field": "commits_authored",'headerName': 'Commits Authored',"sortable":True},
        {"field": "files_authored",'headerName': 'Files Authored',"sortable":True},
]

layout = dbc.Container([
        truck_facto_modal,
         dbc.Modal([
                dbc.ModalHeader([html.I(className="bi bi-git h3 pe-3"),html.Span(f"Commit: ",className="fw-bold"),html.Span(id="commit_modal_header",className="fw-bold")]),
                dbc.ModalBody([
                    dbc.Container([
                        html.P([html.Span("Commit Message: ",className="fw-bold"), html.Span(id="commit_modal_message")] ),
                        html.P([html.Span("Commit Author: ",className="fw-bold"), html.Span(id="commit_modal_author")]),
                        html.P([html.Span("Complete hash string: ",className="fw-bold"),html.Span(id="commit_modal_hash")]),
                        html.P([html.Span("Created at: ",className="fw-bold") ,html.Span(id="commit_modal_date")]),
                        
                    ]),
                ])
            ],id="commit_modal",size="lg"),
        dbc.Row(id="repo_graph_row",children=[
                dbc.Col(
                        [       
                                dcc.Loading([
                                        dbc.Card([
                                                dbc.CardHeader(children=[html.I(className="bi bi-git pe-3 d-inline h2"),html.Span("Project overview",className="fw-bold h2"),html.Br(),
                                                                        ]),
                                                dbc.CardBody(id="general_info"),
                                        ])
                                        
                                ])
                                
                        ]
                ,width=4,align="start"
                ),
                dbc.Col(
                        [
                                dcc.Loading([
                                        dbc.Card([
                                                dbc.CardHeader(children=[
                                                                        html.I(className="bi bi-truck pe-3 d-inline h2"),html.Span("Truck factor",className="fw-bold h2"),
                                                                ]),
                                                dbc.CardBody(id="truck_info"),
                                        ])
                                ])
                        ]
                ,width=4,align="start"
                ),
                dbc.Col(
                        [
                                dbc.Card([
                                                dbc.CardHeader(id="contribution_info_header"),
                                                dbc.CardBody(id="contribution_info"),
                                        ])                                
                        ]
                ,width=4,align="start"
                ),
                ],class_name="pb-4"),
        dbc.Tabs([
                dbc.Tab(
                        [
                        dbc.Row(id="author_graph_row",children=[
                                html.Div([
                                                dcc.RadioItems(id="x_picker",options=[{"label":"Day of week","value":"dow"},{"label":"Per date","value":"date"}],value="dow",inline=True,labelClassName="px-2"),
                                                ]),
                        dbc.Col(
                                [
                                        dcc.Loading(id="author_loader_graph",
                                        children=[dcc.Graph(id="graph",className="h-100")],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                ),
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
                        
                ])
                ],label="General overview"
                ),
                dbc.Tab(label="Authors",children=[
                                        dbc.Row(children=[
                                                dbc.Col(width=12,align="center",id="authors_tab",children=[
                                                AgGrid(
                                                id="authors_table",
                                                columnDefs=column_defs_authors,
                                                columnSize="responsiveSizeToFit",
                                                defaultColDef={"sortable":False,"resizable":True},
                                                dashGridOptions={"pagination": True, "animateRows": False},
                                                )
                                                        ]),
                                        ],justify="center"),]),
                dbc.Tab(label="Commits",children=[                                                  
                                        dbc.Row(children=[
                                                dbc.Col(width=12,align="center",id="commits_tab",children=[
                                                AgGrid(
                                                id="commits_table",
                                                columnDefs=column_defs_commits,
                                                columnSize="responsiveSizeToFit",
                                                defaultColDef={"sortable":False,"resizable":True},
                                                dashGridOptions={"pagination": True, "animateRows": False},
                                                )
                                                        ]),
                                        ],justify="center"),
                                        ]),
                ]),
        # html.Div(id="test-div")
],fluid=True,className="p-10")

@callback(
        Output("general_info","children"),
        Input("authors_cache","data"),
        State("branch_picker","value"),
        State("repo_path","data"),
)
def populate_generale_info(authors,branch,path,):
        rp=RepoMiner(path)
        num_commits=rp.n_commits()
        current_head=rp.git.rev_parse(["--abbrev-ref","HEAD"]) if not branch else branch
        num_authors=len(authors)
        current_commit=rp.get_commit(branch if branch else current_head)
        div=dbc.ListGroup(
                [
                        dbc.ListGroupItem([html.I(className="bi bi-graph-up pe-3 d-inline ms-2"),html.Span(f"Total number of commits: {num_commits}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-pen-fill d-inline ms-2 pe-3"),html.Span(f"Total number of authors: {num_authors}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-signpost-split-fill pe-3 d-inline ms-2"),html.Span(f"Current head of repository: {current_head}")]),
                        dbc.ListGroupItem([html.I(className="bi bi-code-slash pe-3 d-inline ms-2"),html.Span([f"Last reachable commit: ",CommitDisplayerAIO(current_commit).create_comp()])])
                ]
        ,class_name=" py-3",flush=True)
        return html.Div([
                div
        ])

@callback(
        Output("truck_info","children"),
        Input("truck_cache","data"),
        State("contribution_cache","data"),
)
def populate_truck_info(tf,contributions):
        contrs=pd.DataFrame(contributions)
        avg_doa=contrs["DOA"].aggregate("mean")
        div=dbc.ListGroup(
                [       
                        dbc.ListGroupItem([html.Span("Calculated value: "+str(tf),className="ms-2"),html.Br(),]),
                        dbc.ListGroupItem([html.Span("Project's files' avarage DOA: "+str(round(avg_doa,2)),className="ms-2"),html.Br(),]),
                        dbc.ListGroupItem([html.Span("Number of analyzed files: "+str(len(contrs["fname"].unique())),className="ms-2"),html.Br(),])
                ]
        ,class_name=" py-3",flush=True)
        return html.Div([
                div
        ])

@callback(
        Output("commits_table","rowData"),
        Input("branch_cache","data")
)
def populate_commits_tab(data):
        if not data:
                return no_update
        df=pd.DataFrame(data)
        df["date"]=pd.to_datetime(df["date"])
        return df.to_dict("records")

@callback(
        Output("commit_modal_header","children"),
        Output("commit_modal_message","children"),
        Output("commit_modal_author","children"),
        Output("commit_modal_hash","children"),
        Output("commit_modal_date","children"),
        Output("commit_modal","is_open"),
        Input("commits_table","cellClicked"),
        State("branch_cache","data"),
        prevent_initial_call=True
)
def listen_commits_tab_click(cell,data):
        if cell["colId"]!="commit_hash":
                raise PreventUpdate()
        df=pd.DataFrame(data)
        hash=cell["value"]
        commit:pd.Series=df.loc[df["commit_hash"]==hash].iloc[0]
        return hash[:7],commit["subject"],f"{commit['author_name']} <{commit['author_email']}>",hash,commit["date"],True
        
@callback(
        Output("authors_table","rowData"),
        Input("contribution_cache","data"),
        Input("authors_cache","data")
)
def populate_authors_tab(contributions,data,doa_th=0.75):
        if not contributions:
                return no_update
        contr=pd.DataFrame(contributions)
        authors=pd.DataFrame(data)
        contr=contr[contr.DOA >= doa_th]
        contr=contr.groupby("author",as_index=False).count()
        contr.rename(columns={"author":"name"},inplace=True)
        authors=authors.join(contr.set_index("name"),rsuffix="contr",on="name",validate="m:1")
        authors.rename(columns={"DOA":"files_authored"},inplace=True)
        authors["commits_authored"]=authors["commits_authored"].map(lambda a: len(a))
        authors.fillna(0,inplace=True)
        return authors.to_dict("records")

@callback(
        Output("graph","figure"),
        Input("x_picker","value"),
        Input("branch_cache","data"),
        State("branch_picker","value"),
)
def update_count_graph(pick,data,branch):
        if not data:
                return no_update
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
        Input("branch_cache","data"),
)
def update_pie_graph(data,b_cache):
        df=pd.DataFrame(data)
        b_df=pd.DataFrame(b_cache)
        allowed_commits=set(b_df["commit_hash"].to_list())
        df["commits_authored"]=df["commits_authored"].apply(lambda r: set(r).intersection(allowed_commits))
        df["contributions"]=df["commits_authored"].apply(lambda r: len(r))
        df=df.groupby("name",as_index=False).sum(True)
        tot:int=df["contributions"].sum()
        th_percentage=2*tot/100
        df.loc[df['contributions'] < th_percentage, 'name'] = 'Minor contributors total effort'
        fig = px.pie(df, values='contributions', names='name', title='Authors contribution to the project')
        return fig

@callback(
        Output("contribution_info_header","children"),
        Output("contribution_info","children"),
        Input("authors_cache","data"),
        State("contribution_cache","data"),
        prevent_inital_call=True
)
def populate_contributors(authors,contributions,th=0.75):
        if not contributions:
                return no_update
        contrs=pd.DataFrame(contributions)
        auth_df=pd.DataFrame(authors)
        contrs=contrs.loc[contrs["DOA"]>=th]
        top_3=contrs.groupby("author").count().reset_index(drop=False)
        top_3=top_3.sort_values("DOA",ascending=False).head(3)

        i=1
        list_items=[]
        for author in top_3.itertuples("Author"):
                name=author.author
                at=auth_df.loc[(auth_df["name"]==name)]
                tmp_author=dict(name=name,email="",commits_authored=[])
                for a in at.itertuples("At"):
                        tmp_author["email"]=f'{a.email}, {tmp_author["email"]}'.strip()
                        tmp_author["commits_authored"].extend(a.commits_authored)
                nd=AuthorDisplayerAIO(Author(tmp_author["email"],tmp_author["name"],tmp_author["commits_authored"]),contrs.loc[contrs["author"]==name]["fname"].tolist()).create_comp()
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
        div = html.Div(list_group)
        
        return [html.I(className="bi bi-trophy-fill d-inline h3 pe-3"),
                html.H4(f"Your project's top {top_3['DOA'].size} contributors:",className="d-inline fw-bold")],div
