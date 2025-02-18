import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State,clientside_callback,Patch
from src._internal import RepoMiner,make_commit_dataframe,prune_common_commits
import dash.html as html
from datetime import date
import plotly.express as px
import pandas as pd
import dash_ag_grid as dag
from src._internal.data_typing import Author,CommitInfo
from io import StringIO
from logging import getLogger
logger=getLogger("mainpage")
dash.register_page(__name__,"/")
common_labels={"date":"Date","commit_count":"Number of commits","author_email":"Author's email","author_name":"Author's name"}
layout = html.Div([
        dcc.Store(id="commit_df_cache"),
        html.Br(),
        dcc.Dropdown(id="branch_picker",searchable=True,clearable=True,placeholder="Branch name",
                value="all"),
        dcc.Loading(id="author_loader_graph",
                children=[dcc.Graph(id="graph")],
                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                ),
        html.Br(),
        dcc.Loading(id="author_loader",children=[
                dcc.Graph(id="author_graph")
                ],
                overlay_style={"visibility":"visible", "filter": "blur(2px)"},
                display="show")
])
        
@callback(
        Output("commit_df_cache","data"),
        Output("branch_picker","options"),
        Output("graph","figure"),
        Input("branch_picker","value"),
        State("repo_path","data"),
)
def listen_data(v,data):
        # print(data)
        rp=RepoMiner(data)
        max_date=rp.get_commit().date
        m_count=None
        branch=None if not v or "all" == v else v
        commit_df=pd.DataFrame()
        if not branch:
                for commit_list in rp.lazy_load_commits(max_count=m_count):
                        cl_df=pd.concat(map(lambda c:c.get_dataframe(),commit_list))
                        # print(cl_df.info())
                        commit_df=pd.concat([commit_df,cl_df])
        else:
                commit_df=rp.get_branch(branch).get_dataframe()
        commit_df.reset_index(inplace=True)
        commit_df["date"]=pd.to_datetime(commit_df["date"])
        commit_df["dow"]=commit_df["date"].dt.day_name()
        # commit_df.info()
        count_df=commit_df.groupby(["date","author_name","author_email","dow"]).size().reset_index(name="commit_count")
        # print(count_df.columns)
        # print(count_df.head())
        count_df["date"]=pd.to_datetime(count_df["date"])
        # count_df.info()
        count_df["dow"]=count_df["date"].dt.day_name()
        # fig=px.bar(count_df,x="date",y="commit_count",labels=common_labels,title=f"Commit Distribution {branch if branch else ''}",color="author_name",pattern_shape="author_email",pattern_shape_sequence=["+", "x", "."])
        fig=px.bar(count_df,hover_data=["date"],x="dow",y="commit_count",labels=common_labels,title=f"Commit Distribution {branch if branch else ''}",color="author_name",pattern_shape="author_email",pattern_shape_sequence=["+", "x", "."])
        print(fig)
        return commit_df.to_dict("records"),list(( b.name for b in rp.get_branches(deep=False))),fig

@callback(
        Output("author_graph","figure"),
        Output("author_loader","display"),
        Input("commit_df_cache","data"),
        prevent_initial_call=True
)
def populate_author_graph(data):
        df=pd.DataFrame(data)
        # df.info()
        # print(df.head(10))
        count_df=df.groupby(["date","author_name"]).size().sort_index(ascending=True).reset_index(name="commit_count")
        fig=px.bar(count_df,orientation="h",x="commit_count",y="author_name",animation_frame="date",labels=common_labels,color="author_name",title="Author commits effort",range_x=[count_df["commit_count"].min(),count_df["commit_count"].max()])
        return fig,"auto"
