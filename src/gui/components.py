from dash.dcc import DatePickerRange,Graph
from dash import html,Input,Output,callback
from plotly.express import density_heatmap
from plotly.graph_objects import Figure
from git import Commit
from datetime import date
from typing import Literal
SIDING={
    "right":{
        "margin-left": "18rem",
        "margin-right": "2rem"},
    "left":{
            "margin-left": "2rem",
            "margin-right": "18rem",
        }}
# the style arguments for the sidebar. We use position:fixed and a fixed width
SIDEBAR_STYLE = {
    "position": "fixed",
    "top": 0,
    "bottom": 0,
    "width": "16rem",
    "padding": "2rem 1rem",
    "background-color": "#f8f9fa",
}

# the styles for the main content position it to the right of the sidebar and
# add some padding.
CONTENT_STYLE = {
    "margin-left": "18rem",
    "margin-right": "2rem",
    "padding": "2rem 1rem",
}

def sidebar(side:Literal["right","left"]="right")->html.Div:
    if side != "right" and side != "left":
        raise ValueError()
    elif side == "left":
        SIDEBAR_STYLE["left"]=0
    else:
        SIDEBAR_STYLE["right"]=0
    return html.Div(
        style=SIDEBAR_STYLE
    )
