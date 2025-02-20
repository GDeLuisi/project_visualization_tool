from dash.dcc import DatePickerRange,Graph
from dash import html,Input,Output,callback
from plotly.express import density_heatmap
from plotly.graph_objects import Figure
from git import Commit
from datetime import date
def create_start_page():
    html.Div([
        
    ])
def create_commit_heatmap(commits:Commit,start_date:date,end_date:date):
    date_picker=DatePickerRange(id="date_picker",start_date=start_date,end_date=end_date)
    density_heatmap(commits)
# def create_datepicker(start_date:date,end_date:date)->DatePickerRange:
#     return DatePickerRange(id="date_picker",start_date=start_date,end_date=end_date)

# @callback(
#     Output('output-container-date-picker-range', 'children'),
#     Input('my-date-picker-range', 'start_date'),
#     Input('my-date-picker-range', 'end_date'))
# def update_output(start_date, end_date):
#     string_prefix = 'You have selected: '
#     if start_date is not None:
#         start_date_object = date.fromisoformat(start_date)
#         start_date_string = start_date_object.strftime('%B %d, %Y')
#         string_prefix = string_prefix + 'Start Date: ' + start_date_string + ' | '
#     if end_date is not None:
#         end_date_object = date.fromisoformat(end_date)
#         end_date_string = end_date_object.strftime('%B %d, %Y')
#         string_prefix = string_prefix + 'End Date: ' + end_date_string
#     if len(string_prefix) == len('You have selected: '):
#         return 'Select a date to see it displayed here'
#     else:
#         return string_prefix
