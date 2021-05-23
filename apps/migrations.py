from dash_bootstrap_components._components.CardBody import CardBody
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

from sklearn.preprocessing import LabelEncoder

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

# Sankey plot (migration flow chart)

flow = pd.read_csv("Barcelona_data/immigrants_emigrants_by_destination.csv")
emigration = flow[flow['from'].str.contains("Barcelona")]
immigration = flow[flow['to'].str.contains("Barcelona")]


def draw_migration(from_or_to=None):
    dataset = flow
    if from_or_to == "immigration":
        dataset = immigration
    elif from_or_to == "emigration":
        dataset = emigration

    label_encoder = LabelEncoder()
    encoding = label_encoder.fit(flow['from'])
    source = label_encoder.transform(dataset['from'])
    target = label_encoder.transform(dataset['to'])
    label = label_encoder.classes_
    value = immigration['weight']

    link = dict(source=source, target=target, value=value)
    node = dict(label=label)
    sankey = go.Sankey(link=link, node=node)

    fig = go.Figure(sankey)
    return fig

# Datatable
flow_by_sex = pd.read_csv("Barcelona_data/immigrants_emigrants_by_sex.csv")
flow_by_sex.drop(columns=['Neighborhood Name', 'Neighborhood Code'], inplace=True)
flow_by_sex = flow_by_sex.groupby(by=["Year", "District Name", 'Gender']).sum()
flow_by_sex = flow_by_sex.reset_index()
flow_by_sex['Gender'] = flow_by_sex.Gender.astype("category")
flow_by_sex.drop(columns=['District Code'], inplace=True)


def population_change(row):
    if row['Immigrants']/row['Emigrants'] < 1.3:
        return "slight increase"
    elif row["Immigrants"]/row['Emigrants'] < 1.4:
        return "moderate increase"
    else:
        return "high increase"


flow_by_sex['Change in population'] = flow_by_sex.apply(lambda row: population_change(row), axis=1)


def migration_by_district_table():
    table = dash_table.DataTable(
        id='datatable_interactive',
        columns=[
            {"name": i, 'id': i, "deletable": False, "selectable": False} for i in flow_by_sex.columns
        ],
        data=flow_by_sex.to_dict('records'),
        filter_action="native",
        sort_action="native",
        sort_mode='single',
        page_action="none",
        style_table={
            'height': '300px',
            'overflowY': 'auto'
        },
        style_data={
            'whiteSpace': 'normal',
            'height': 'auto'
        },
        style_cell_conditional=[
            {'if': {'column_id': c},
             'textAlign': 'left'}
            for c in []
        ]
    )
    return table

layout = dbc.Container([
    ### PART CONCERNING DEMOGRAPHICS
    dbc.Row([
        dbc.Col([
            dbc.CardBody([
                html.H2("City Demographics - Births & Deaths", style={'text-align':'left', 'color':'red'})
            ])
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(
                        id='births_district',
                        options=districts,
                        placeholder='Select district'

                    ),
                    dcc.Graph(
                        id='births_graph',
                        figure=births_fig
                    )
                ])
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(
                        id='deaths_district',
                        options = districts,
                        placeholder = 'Select district'

                    ),
                    dcc.Graph(
                        id='deaths_graph',
                        figure=deaths_fig
                    )
                ])
            ])
        ], width=8)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H2("Migrations & population", style={'text-align':'left', 'color':'red'})
                ])
            ])
        ], width=12)
    ]),
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Dropdown(
                        id="migration_dropdown",
                        options=[
                            {'label': 'all', 'value': 'all'},
                            {'label': 'immigration', "value": "immigration"},
                            {'label': 'emigration', 'value': 'emigration'}
                        ],
                    ),
                    dcc.Graph(
                        id='migration_sankey',
                        figure=draw_migration()
                    )
                ])
            ])
        ], width=7),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        migration_by_district_table()
                    ])
                ])
            ])
        ], width=12-7)
    ]),


], fluid=True)


@app.callback(
    Output('births_graph', 'figure'),
    Input('births_district', 'value')
)
def redraw_birth_graph(district):
    df = births_df
    if district is None:
        location = 'Barcelona'
    else:
        df = df[df['District Name'] == district]
        location = district

    df = df.groupby(["Year", "Gender"])['Number'].sum().reset_index(name='Number')
    df.sort_values(by=['Year'], inplace=True)

    fig = px.bar(df, x = 'Year', y = 'Number', color = 'Gender', barmode = 'group', title = 'Births in {}'.format(location))
    fig.update_layout(
        title = {
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    return fig

@app.callback(
    Output('deaths_graph', 'figure'),
    Input('deaths_district', 'value')
)
def redraw_birth_graph(district):
    df = deaths_df
    if district is None:
        location = 'Barcelona'
    else:
        df = df[df['District.Name'] == district]
        location = district

    df = df.groupby(["Year", "Age"])['Number'].sum().reset_index(name='Number')
    df.sort_values(by=['Year', 'Age'], inplace=True)

    fig = px.bar(df, x = 'Year', y = 'Number', color = 'Age', barmode = 'group', title = 'Deaths in {}'.format(location), log_y=True)
    fig.update_layout(
        title = {
            'y':0.9,
            'x':0.5,
            'xanchor': 'center',
            'yanchor': 'top'
        }
    )
    return fig

@app.callback(
    Output(component_id='migration_sankey', component_property='figure'),
    Input(component_id='migration_dropdown', component_property='value')
)
def update_migration_chart(dropdown_selection):
    migration = draw_migration(dropdown_selection)
    return migration
