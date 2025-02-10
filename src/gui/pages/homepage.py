import dash
from dash import dcc
import dash.html as html
from datetime import date
import plotly.express as px

dash.register_page(__name__,"/")

layout = html.Div([
        dcc.DatePickerRange(
            id='my-date-pick-range',
            min_date_allowed=date(1995, 8, 5),
            max_date_allowed=date(2017, 9, 19),
            initial_visible_month=date(2017, 8, 5),
            end_date=date(2017, 8, 25)
        ),
        html.Div(id='output-container-date-picker-range')
        ])

