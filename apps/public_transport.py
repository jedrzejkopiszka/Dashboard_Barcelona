import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import json

import dash  # (version 1.12.0) pip install dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import dash_table

import dash_leaflet as dl
import dash_leaflet.express as dlx


mapbox_access_token = "pk.eyJ1IjoiYW5kcmV3a29waXN6a2EiLCJhIjoiY2tvenVjNGRqMGhhODJ2bnpydWpvaWxhMiJ9.byTREleNujikHzUe1BameA"

from app import app

def h24_to_h12(hour: int) -> str:
    r = hour % 12
    if r == 0:
        r = 12
    if hour < 12:
        return "{}am".format(r)
    else:
        return "{}pm".format(r)


def get_accident_data(acc_df):
    acc_df = acc_df[['Latitude', 'Longitude']]
    dicts = acc_df.to_dict('rows')
    accident_geojson = dlx.dicts_to_geojson(dicts, lon='Longitude', lat="Latitude")
    # accident_geobuf = dlx.geojson_to_geobuf(accident_geojson)
    return accident_geojson

### LOGIC OF DEMOGRAPHICS

districts = [
    {'label': 'Ciutat Vella', 'value': 'Ciutat Vella'},
    {'label': 'Eixample', 'value': 'Eixample'},
    {'label': 'Sants-Montjuïc', 'value': 'Sants-Montjuïc'},
    {'label': 'Les Corts', 'value': 'Les Corts'},
    {'label': 'Sarrià-Sant Gervasi', 'value': 'Sarrià-Sant Gervasi'},
    {'label': 'Gràcia', 'value': 'Gràcia'},
    {'label': 'Horta-Guinardó', 'value': 'Horta-Guinardó'},
    {'label': 'Nou Barris', 'value': 'Nou Barris'},
    {'label': 'Sant Andreua', 'value': 'Sant Andreu'},
    {'label': 'Sant Martí', 'value': 'Sant Martí'}
]

age_groups = ["{}-{}".format(x, x+4) for x in range(0, 99, 5)]
age_groups.append(">=100")

births_df = pd.read_csv("Barcelona_data/births.csv")

births_graph_df = births_df.groupby(["Year", "Gender"])['Number'].sum().reset_index(name='Number')
births_graph_df.sort_values(by=['Year'], inplace=True)

births_fig = px.bar(births_graph_df, x = 'Year', y = 'Number', color = 'Gender', barmode = 'group', title = 'Births in Barcelona')
births_fig.update_layout(
    title = {
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)

deaths_df = pd.read_csv("Barcelona_data/deaths.csv")
deaths_df["Age"] = pd.Categorical(
    deaths_df["Age"],
    categories=age_groups,
    ordered=True
)

deaths_graph_df = deaths_df.groupby(["Year", "Age"])['Number'].sum().reset_index(name='Number')
deaths_graph_df.sort_values(by=['Year', 'Age'], inplace=True)

deaths_fig = px.bar(deaths_graph_df, x = 'Year', y = 'Number', color = 'Age', barmode = 'group', title = 'Deaths in Barcelona', log_y=True)
deaths_fig.update_layout(
    title = {
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    }
)
### LOGIC OF ACCIDENTS

accident_df = pd.read_csv("Barcelona_data/accidents_2017.csv")

accident_df['Weekday'] = pd.Categorical(
    accident_df['Weekday'],
    categories=['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday', 'Sunday'],
    ordered=True)

accident_df['Part of the day'] = pd.Categorical(
    accident_df['Part of the day'],
    categories=['Morning', 'Afternoon', 'Night'],
    ordered=True)

accident_df['Hour'] = accident_df['Hour'].apply(lambda x: h24_to_h12(x))
accident_df['Hour'] = pd.Categorical(
    accident_df['Hour'],
    categories=[h24_to_h12(x) for x in range(24)],
    ordered=True)

# initial graphs
accident_weekdays_df = accident_df.groupby("Weekday")['Id'].count().reset_index(name='Accidents')
accident_weekdays_df.sort_values(by='Weekday', inplace=True)

accident_weekdays_fig = px.bar_polar(accident_weekdays_df, theta='Weekday', r='Accidents', title="Accidents in Barcelona in 2017")
accident_weekdays_fig.update_layout(
    title = {
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    margin = {
        'l': 5, 'r': 5
    },
    polar = {
        'radialaxis': {
            'showticklabels': False
        }
    }
)

accident_hours_df = accident_df.groupby("Hour")['Id'].count().reset_index(name='Accidents')
accident_hours_df.sort_values(by='Hour', inplace=True)

accident_hours_fig = px.bar_polar(accident_hours_df, theta='Hour', r='Accidents', title="Accidents by hours", log_r=True)
accident_hours_fig.update_layout(
    title = {
        'y':0.9,
        'x':0.5,
        'xanchor': 'center',
        'yanchor': 'top'
    },
    margin = {
        'l': 5, 'r': 5
    },
    polar = {
        'radialaxis': {
            'showticklabels': False
        }
    }
)

accident_geojson = dl.GeoJSON(
    data = get_accident_data(accident_df), id = 'accident_geojson', format = 'geojson',
        zoomToBounds = True, cluster = True, zoomToBoundsOnClick = True, superClusterOptions = {'radius': 100})

# Logics behind transports
transport_data = pd.read_csv('Barcelona_data/transports.csv')
transport_options_checklist = [{'label': str(b), 'value': b} for b in sorted(transport_data.Transport.unique())]
transport_value_checklist = [b for b in sorted(transport_data.Transport.unique())]


def apply_color_transport(category):
    if category == "Airport train":
        return "green"
    elif category == 'Cableway':
        return "red"
    elif category == "Funicular":
        return "orange"
    elif category == "Maritime station":
        return "blue"
    elif category == "RENFE":
        return "yellow"
    elif category == "Railway (FGC)":
        return "black"
    elif category == "Tram":
        return "lightblue"
    else:
        return "brown"


transport_data['Color'] = transport_data.Transport.apply(lambda x: apply_color_transport(x))


def draw_transport_map(checklist_transport_providers=None):
    if checklist_transport_providers is not None:
        df_sub = transport_data[transport_data.Transport.isin(checklist_transport_providers)]
    else:
        df_sub = transport_data
    # Create figure
    locations = [go.Scattermapbox(
        lon=df_sub['Longitude'],
        lat=df_sub['Latitude'],
        mode='markers',
        unselected={'marker': {'opacity': 1}},
        selected={'marker': {'opacity': 0.5, 'size': 25}},
        hoverinfo='text',
        hovertext=df_sub.Transport,
        marker={'color': df_sub.Color}
    )]

    # Return figure
    return {
        'data': locations,
        'layout': go.Layout(
            uirevision='foo',  # preserves state of figure/map after callback activated
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            margin=dict(t=20, l=0, r=0, b=0),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=25,
                style='light',
                center=dict(
                    lat=41.390205,
                    lon=2.154007
                ),
                pitch=0,
                zoom=11.5
            ),
        )
    }

# Bus stops
bus_stop_data = pd.read_csv("Barcelona_data/bus_stops.csv")
bus_stop_data.drop(columns=['Code', 'Bus.Stop'], inplace=True)


def apply_color(category):
    if category == "Day bus stop":
        return "yellow"
    elif category == 'Night bus stop':
        return "blue"
    elif category == "Airport bus stop":
        return "red"
    else:
        return "green"


bus_stop_data['Color'] = bus_stop_data.Transport.apply(lambda x: apply_color(x))


def draw_bus_stop_map(checklist_bus_stops):
    bus_stop = bus_stop_data[bus_stop_data.Transport.isin(checklist_bus_stops)]

    # Create figure
    locations = [go.Scattermapbox(
        lon=bus_stop['Longitude'],
        lat=bus_stop['Latitude'],
        mode='markers',
        unselected={'marker': {'opacity': 0.7, 'size':20}},
        selected={'marker': {'opacity': 0.5, 'size': 25}},
        hoverinfo='text',
        hovertext=bus_stop["District.Name"],
        marker={'color': bus_stop.Color}
    )]

    # Return figure
    return {
        'data': locations,
        'layout': go.Layout(
            uirevision='foo',
            clickmode='event+select',
            hovermode='closest',
            hoverdistance=2,
            margin=dict(t=20, b=0, l=0, r=0),
            mapbox=dict(
                accesstoken=mapbox_access_token,
                bearing=25,
                style='light',
                center=dict(
                    lat=41.390205,
                    lon=2.154007
                ),
                pitch=0,
                zoom=11.5
            ),
        )
    }


layout = dbc.Container([
    ### PART CONCERNING ACCIDENTS
    dbc.Row([
        dbc.Col([
            dbc.CardBody([
                html.H2("Road Safety & Accidents", style={'text-align':'left', 'color':'red'})
            ])
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        id='accident_weekday_graph',
                        figure=accident_weekdays_fig
                    ),
                    html.H4(["Selected weekday: None"], id='weekday_msg'),
                    html.Button('Reset weekday',id='reset_weekday_button', n_clicks = 0)
                ], style={'height': '100%'})
            ], style={'height': '100%'})
        ], width=3, style={'height': '100%'}),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        id='accident_hour_graph',
                        figure=accident_hours_fig
                    ),
                    html.H4(["Selected hour: None"], id='hour_msg'),
                    html.Button('Reset hour',id='reset_hour_button', n_clicks = 0)
                ], style={'height': '100%'})
            ], style={'height': '100%'})
        ], width=3, style={'height': '100%'}),
        dbc.Col([
            dl.Map([dl.TileLayer(), accident_geojson], center=(41.3947, 2.0787), zoom=11, style={'width': '100%', 'height': '100%', 'margin': "auto", "display": "block"})
        ], width=6, style={'height': '100%'})
    ], style={'height': '60vh', 'min-height': '560px', 'max-height':'650px'}),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("Transport system", style={'text-align':'left', 'color':'red'})
                ])
            ])
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Checklist(
                        id="transport_checklist",
                        options=transport_options_checklist,
                        value=transport_value_checklist,
                        inputStyle={'margin-left':"20px"}
                    ),
                    dcc.Graph(
                        id="transport_map",
                        figure={}
                    )
                ])
            ])
        ], width=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Checklist(
                        id='bus_stop_checklist',
                        options=[
                            {'label': 'Day bus stop', "value": "Day bus stop"},
                            {'label': 'Night bus stop', 'value': 'Night bus stop'},
                            {'label': 'Airport bus stop', "value": "Airport bus stop"},
                            {'label': 'Bus station', 'value': 'Bus station'},
                        ],
                        value=['Day bus stop'],
                        inputStyle={'margin-left':'20px'}
                    ),
                    dcc.Graph(
                        id='bus_stop_map',
                        figure={}
                    )
                ])
            ])
        ])
    ]),
], fluid=True)


@app.callback(
    Output('accident_weekday_graph', 'clickData'),
    Input('reset_weekday_button', 'n_clicks')
)
def reset_accident_day_selection(resetClick):
    return None

@app.callback(
    Output('accident_hour_graph', 'clickData'),
    Input('reset_hour_button', 'n_clicks')
)
def reset_accident_day_selection(resetClick):
    return None

@app.callback(
    Output('weekday_msg', 'children'),
    Input('accident_weekday_graph', 'clickData')
)
def update_weekday_msg(clickData):
    if clickData is None:
        weekday = 'None'
    else:
        weekday = clickData['points'][0]['theta']
    return "Selected weekday: {}".format(weekday)

@app.callback(
    Output('hour_msg', 'children'),
    Input('accident_hour_graph', 'clickData')
)
def update_weekday_msg(clickData):
    if clickData is None:
        hour = 'None'
    else:
        hour = clickData['points'][0]['theta']
    return "Selected hour: {}".format(hour)


@app.callback(
    Output('accident_hour_graph', 'figure'),
    Input('accident_weekday_graph', 'clickData')
)
def redraw_hour_graph(clickData):
    if clickData is None:
        df = accident_df
        title = 'Accidents by hours'
    else:
        weekday = clickData['points'][0]['theta']
        df = accident_df[accident_df['Weekday'] == weekday]
        title = 'Accidents on {}s by hours'.format(weekday)

    df = df.groupby("Hour")['Id'].count().reset_index(name='Accidents')
    df.sort_values(by='Hour', inplace=True)

    fig = px.bar_polar(df, theta='Hour', r='Accidents', title=title, log_r=True)
    fig.update_layout(
        title = {
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        polar = {
            'radialaxis': {
                'showticklabels': False
            }
        }
    )
    return fig

@app.callback(
    Output('accident_weekday_graph', 'figure'),
    Input('accident_hour_graph', 'clickData')
)
def redraw_hour_graph(clickData):
    if clickData is None:
        df = accident_df
        title = 'Accidents by weekdays'
    else:
        hour = clickData['points'][0]['theta']
        df = accident_df[accident_df['Hour'] == hour]
        title = 'Accidents at {} by weekdays'.format(hour)

    df = df.groupby("Weekday")['Id'].count().reset_index(name='Accidents')
    df.sort_values(by='Weekday', inplace=True)

    fig = px.bar_polar(df, theta='Weekday', r='Accidents', title=title)
    fig.update_layout(
        title = {
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        },
        polar = {
            'radialaxis': {
                'showticklabels': False
            }
        }
    )
    return fig


@app.callback(
    Output('accident_geojson', 'data'),
    Input('accident_weekday_graph', 'clickData'),
    Input('accident_hour_graph', 'clickData')
)
def update_accident_map(weekday_data, hour_data):
    df = accident_df
    if weekday_data is not None:
        weekday = weekday_data['points'][0]['theta']
        df = df[df['Weekday'] == weekday]
    if hour_data is not None:
        hour = hour_data['points'][0]['theta']
        df = df[df['Hour'] == hour]
    return get_accident_data(df)


@app.callback(
    Output(component_id='transport_map', component_property='figure'),
    Input(component_id='transport_checklist', component_property='value')
)
def update_transport_map(transport_checklist):
    return draw_transport_map(transport_checklist)

@app.callback(
    Output(component_id='bus_stop_map', component_property='figure'),
    Input(component_id='bus_stop_checklist', component_property='value')
)
def update_bus_stops_map(bus_stop_checklist):
    return draw_bus_stop_map(bus_stop_checklist)

