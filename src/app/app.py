from webbrowser import open
from dash import Dash,html,dcc,page_container,Input,Output,callback,no_update
from typing import Union,Optional
from datetime import date
from pathlib import Path
from waitress import serve
from src._internal import RepoMiner
from time import strptime,strftime
import pandas as pd
import numpy as np
import plotly.express as px
from src._internal import make_commit_dataframe

df=None
# from gui import create_datepicker
def start_app(repo_path:Union[str|Path]):
    global df
    repo=RepoMiner(repo_path=repo_path)
    df=make_commit_dataframe(reversed(repo.commit_list))
    # print(df.head())
    dff=df.copy()
    dff["date_show"]=df["date"].map(lambda date_in:date_in.isoformat())
    start=dff["date_show"].head(1).iloc[0]
    end=dff["date_show"].tail(1).iloc[0]
    print(start,end)
    # dff=df.copy()
    # counts, bins = np.histogram(df.date)
    # fig = px.bar(x=bins, y=counts, labels={'x':'total_bill', 'y':'count'})
    fig=px.density_heatmap(dff,"date_show","author_name","hash",histfunc="count")
    # fig.update_layout(bargap=0.4,yaxis_title="commits per day",xaxis_title="date")
    # fig.update_xaxes(range=[start, end])
    app=Dash(name="Project Visualization Tool",title="PVT",use_pages=True,pages_folder=Path(__file__).parent.parent.joinpath("gui","pages").as_posix(),assets_folder=Path(__file__).parent.parent.joinpath("gui","assets").as_posix())
    app.layout = html.Div([
        dcc.DatePickerRange(
            id='my-date-picker-range',
            min_date_allowed=date.fromisoformat(start),
            max_date_allowed=date.fromisoformat(end),
            initial_visible_month=date.fromisoformat(start)
    ),
    dcc.Graph(id="graph",figure=fig),
    html.Div(id='output-container-date-picker-range'),
    page_container
    ])
    open("http://localhost:8050/")
    serve(app.server,host="localhost",port=8050)
    
# @callback(
#     Output('output-container-date-picker-range', 'children'),
#     Output('graph', 'figure'),
#     Input('my-date-picker-range', 'start_date'),
#     Input('my-date-picker-range', 'end_date'))
# def update_output(start_date, end_date):
#     string_prefix = 'You have selected: '
#     dff=df.copy()
#     if start_date is not None:
#         start_date_object = date.fromisoformat(start_date)
#         start_date_string = start_date_object.strftime('%d %b %Y')
#         string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
#     if end_date is not None:
#         end_date_object = date.fromisoformat(end_date)
#         end_date_string = end_date_object.strftime('%d %b %Y')
#         string_prefix = string_prefix + 'End Date: ' + end_date_string
#     if start_date and end_date:
#         dff=dff[(dff['date'] >= start_date_object) & (dff['date'] <= end_date_object)]
#         print(dff.head(10))
#         fig=px.histogram(dff,"date","author",histfunc="count",labels={'x':'date', 'y':'commits per day'})
#         return string_prefix,fig
#     else: 
#         return no_update,no_update
