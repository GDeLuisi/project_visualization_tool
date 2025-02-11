import dash
from dash import dcc,callback,Input,Output,no_update,set_props,State
from src._internal import RepoMiner,make_commit_dataframe
import dash.html as html
from datetime import date
import plotly.express as px
import pandas as pd
import dash_ag_grid as dag
from io import StringIO

dash.register_page(__name__,"/")

        # dcc.DatePickerRange(
        #     id='my-date-pick-range',
        #     min_date_allowed=date(1995, 8, 5),
        #     max_date_allowed=date(2017, 9, 19),
        #     initial_visible_month=date(2017, 8, 5),
        #     end_date=date(2017, 8, 25)
        # ),
layout = html.Div([
        html.Button(id="click_me",children=["Load Data"]),
        dcc.DatePickerRange(
                id='my-date-pick-range',
                min_date_allowed=date(1995, 8, 5),
                max_date_allowed=date(2017, 9, 19),
                initial_visible_month=date(2017, 8, 5),
                end_date=date(2017, 8, 25)
        ),
        dag.AgGrid("main_grid",dashGridOptions={'pagination':True}),
        dcc.Graph(id="graph")
        ])

@callback(
        Output("commit_df","data"),
        State("repo_path","data"),
        Input("click_me","n_clicks"),
        prevent_initial_call=True,
        background=True
)
def listen_data(data,nclick):
        # print(data)
        rp=RepoMiner(data)
        commit_df=make_commit_dataframe([])
        columns=[{"headerName":i,"field":i,"filter":i != "date"} for i in commit_df.columns if i != "files_modified" and i!="parent"and i!="refs"]
        for commit_list in rp.lazy_load_commits():
                # print(commit_list)
                n_commit_df=make_commit_dataframe(commit_list=commit_list)
                commit_df=pd.concat([commit_df,n_commit_df])
                # print(n_commit_df.head())
                set_props("main_grid",{"rowData":commit_df.to_dict("records"),"columnDefs":columns})
        # print(commit_df.head(5))
        commit_df.reset_index(inplace=True)
        return commit_df.to_json()
