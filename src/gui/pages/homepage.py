import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch,ctx,MATCH
from dash.exceptions import PreventUpdate
import dash.html as html
import plotly.express as px
import pandas as pd
from src.app.helper import create_info_card_columns
from repository_miner import RepoMiner
from src._internal.data_typing import Author
import dash_bootstrap_components as dbc
from dash_ag_grid import AgGrid
from src.gui import AuthorDisplayerAIO,CommitDisplayerAIO
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
        dbc.Tooltip("Click on the commit hash for commit description",target="commit_tooltip",trigger="legacy",is_open=False,id="commit_tooltip_info"),
        dbc.Tooltip("Choose a range to filter out all the authors that are out of commit count range",target="commit_slider",is_open=False,placement="top-end",trigger="hover legacy"),

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
        dbc.Row(id="repo_general_overview_row",class_name="mb-3"),
        dbc.Row(id="repo_graph_row",children=[
                
                dbc.Col(
                        [
                                dcc.Loading([
                                        dbc.Card([
                                                dbc.CardHeader(children=[
                                                                        html.I(className="bi bi-clipboard2-data pe-3 d-inline h2"),html.Span("Repository analysis",className="fw-bold h2"),
                                                                ]),
                                                dbc.CardBody(id="repo_info",children=[
                                                        dcc.Loading(id="author_overview_loader",children=[
                                                         dcc.Graph(id="repo_info_graph")
                                                                ],
                                                                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                                                ),
                                                                
                                                ]),
                                        ])
                                ])
                        ]
                ,width=6,align="start"
                ),
                dbc.Col(
                        [
                                dbc.Card([
                                                dbc.CardHeader(id="contribution_info_header",children=[
                                                        html.I(className="bi bi-truck d-inline h2 pe-3"),
                                                        html.H4(f"Truck factor",className="d-inline fw-bold h2")
                                                ]),
                                                dbc.CardBody(id="contribution_info",children=[
                                                        dcc.Loading(id="author_overview_loader",children=[
                                                         dcc.Graph(id="contribution_graph")
                                                        ],
                                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                                        ),
                                                        
                                                ]),
                                        ])                                
                        ]
                ,width=6,align="start"
                ),
                ],class_name="pb-4"),
        dbc.Tabs([
                dbc.Tab(
                        [
                        dbc.Row(id="author_graph_row",children=[           
                        dbc.Col(
                                [
                                        dbc.RadioItems(id="x_picker",options=[{"label":"Day of week","value":"dow"},{"label":"Per date","value":"date"}],value="dow",inline=True, switch=True),
                                        dcc.Loading(id="author_loader_graph",
                                        children=[dcc.Graph(id="graph",className="h-100")],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                ),
                                ],width=7,align="center"),
                        dbc.Col([
                                 dbc.RadioItems(
                                        options=[
                                                {"label": "Pie graph", "value": "pie"},
                                                {"label": "Scatter Plot", "value": "scatter"},
                                        ],
                                        value="scatter",
                                        id="author_graph_picker",
                                        switch=True,
                                        inline=True,
                                        ),
                                dcc.Loading(id="author_overview_loader",children=[
                                                dcc.Graph(id="author_overview")
                                        ],
                                        overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                                        ),
                                
                                ],width=4),
                        dbc.Col(width=1,children=[
                                dcc.RangeSlider(min=1,max=10,id="commit_slider",value=[1,10],vertical=True,tooltip={"placement": "bottom", "always_visible": False})
                        ]),
                                
                        ],justify="center"),
                dbc.Row([
                        
                ])
                ],label="History overview"
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
                                        html.I(id="commit_tooltip",className="bi bi-question fw-bold fs-3 clickable"),                                                  
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
        Output("repo_general_overview_row","children"),
        Input("authors_cache","data"),
        State("contribution_cache","data"),
        State("branch_picker","value"),
        State("repo_path","data"),
)
def populate_generale_info(authors,contributions,branch,path,):
        rp=RepoMiner(path)
        contrs=pd.DataFrame(contributions)
        num_commits=rp.n_commits()
        current_head=rp.git.rev_parse(["--abbrev-ref","HEAD"]) if not branch else branch
        num_authors=len(authors)
        current_commit=rp.get_commit(branch if branch else current_head)
        local_branches_num=len(rp.local_branches_list())
        tag_num=len(list(rp.get_tags()))
        texts={
                "Total number of commits":f"{num_commits}",
                "Total number of authors":f"{num_authors}",
                # f"Current head of repository: {current_head}",
                "Number of branches":f"{local_branches_num}",
                "Number of tags":f"{tag_num}",
                "Number of files of interest":f"{str(len(contrs['fname'].unique()))}",
                "Last reachable commit":CommitDisplayerAIO(current_commit).create_comp()
        }
        icons={
                "Total number of commits":html.I(className="bi bi-graph-up pe-3 d-inline ms-2 h4 fw-bold text-start"),
                "Total number of authors":html.I(className="bi bi-pen-fill d-inline ms-2 pe-3"),
                "Number of branches":html.I(className="bi bi-bezier2 pe-3 d-inline ms-2"),
                "Number of tags":html.I(className="bi bi bi-tags pe-3 d-inline ms-2"),
                "Number of files of interest":html.I(className="bi bi-search pe-3 d-inline ms-2"),
                "Last reachable commit":html.I(className="bi bi-code-slash pe-3 d-inline ms-2")
        }
        cards:list=create_info_card_columns(texts,icons)
        return cards
        
       
        

@callback(
        Output("repo_info_graph","figure"),
        Input("contribution_cache","data"),
)
def populate_repo_info(contributions):
        def extract_suffix(filename:str)->str:
                try:
                        return filename.rsplit(".",maxsplit=1)[1]
                except IndexError:
                        return "no extension"
        contrs=pd.DataFrame(contributions)
        fnames=contrs["fname"].unique()
        suffixes=[extract_suffix(f) for f in fnames]
        df=pd.DataFrame(dict(fname=fnames,suffix=suffixes))
        df=df.groupby("suffix",as_index=False).count()
        # print(df.head(999))
        tot:int=df["fname"].sum()
        th_percentage=3*tot/100
        df.loc[df['fname'] < th_percentage, 'suffix'] = 'Other'
        fig = px.pie(df, values='fname', names='suffix',labels={"fname":"files"},hole=0.5)
        fig.update_layout(annotations=[dict(text='Languages',
                      font_size=20, showarrow=False, xanchor="center")])
        return fig

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
        Input("author_graph_picker","value"),
        Input("commit_slider","value"),
        State("contribution_cache","data"),
)
def update_pie_graph(data,b_cache,pick,range,contribution):
        df=pd.DataFrame(data)
        b_df=pd.DataFrame(b_cache)
        allowed_commits=set(b_df["commit_hash"].to_list())
        df["commits_authored"]=df["commits_authored"].apply(lambda r: set(r).intersection(allowed_commits))
        df["contributions"]=df["commits_authored"].apply(lambda r: len(r))
        df=df.groupby("name",as_index=False).sum(True)
        min,max=range
        mask = (df['contributions'] >= min) & (df['contributions'] <= max)
        df=df[mask]
        if pick =="pie":
                tot:int=df["contributions"].sum()
                th_percentage=2*tot/100
                df.loc[df['contributions'] < th_percentage, 'name'] = 'Minor contributors total effort'
                fig = px.pie(df, values='contributions', names='name', title='Authors commit distribution')
        else:
                contrs=pd.DataFrame(contribution)
                contrs=contrs.groupby("author").sum()
                df=df.join(contrs,rsuffix="contr",on="name",validate="m:1").reset_index()
                fig = px.scatter(df,x="name",y="contributions",color="tot_contributions",title='Authors commit distribution', labels={"contributions":"commit count","tot_contributions":"contributions"})
                fig.update_xaxes(showticklabels=False)
                fig.update_yaxes(gridcolor='lightgrey')
                fig.update_layout(
                        plot_bgcolor='white'
                )
        return fig
@callback(
      Output("commit_slider","max"),
      Output("commit_slider","value"),  
      Input("authors_cache","data"),
      Input("branch_cache","data"),         
)

def setup_slider(data,b_cache):
        df=pd.DataFrame(data,)
        b_df=pd.DataFrame(b_cache)
        allowed_commits=set(b_df["commit_hash"].to_list())
        df["commits_authored"]=df["commits_authored"].apply(lambda r: set(r).intersection(allowed_commits))
        df["contributions"]=df["commits_authored"].apply(lambda r: len(r))
        df=df.groupby("name",as_index=False).sum(True)
        max= df["contributions"].max()
        return max , [1,max]

@callback(
        Output("contribution_graph","figure"),
        Input("truck_cache","data"),
        State("contribution_cache","data"),
        prevent_inital_call=True
)
def populate_contributors(tf,contributions,th=0.75):
        if not contributions:
                return no_update
        contrs=pd.DataFrame(contributions)
        contrs=contrs.loc[contrs["DOA"]>=th]
        top=contrs.groupby("author",as_index=False).count()
        top=top.sort_values("DOA",ascending=False).head(tf)
        tot:int=top["DOA"].sum()
        th_percentage=3*tot/100
        top.loc[top['DOA'] < th_percentage, 'author'] = 'Other contributors'
        # print(top.head(tf))
        fig = px.pie(top, values='DOA', names='author',labels={"DOA":"files authored"},hole=0.4)
        fig.update_layout(annotations=[dict(text=tf,
                      font_size=20, showarrow=False, xanchor="center")])
        return fig

@callback(
        Output("commit_tooltip_info","is_open"),
        Input("commit_tooltip","n_clicks"),
        prevent_inital_call=True
)
def open_toast_commit(_):
        if _==None:
                return no_update
        return True