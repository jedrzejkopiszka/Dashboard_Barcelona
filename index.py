import dash_core_components as dcc
import dash_html_components as html
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
from app import app
from app import server

from apps import public_transport, migrations

app.layout = html.Div([
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H1("Barcelona - Urban Analysis", style={'text-align':'left', 'color':'red'}),
                    dcc.Location(id='url', refresh=False),
                    html.P(['Our dashboard presents an analysis of a variety of data from the breath-taking city of Barcelona, focusing on city demographics and safety of transport.'], style={'font-size': '1.2em'}),
                    dbc.Row([
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Link('Demographics', href='/apps/migrations', style={'size': '1.5ex', 'font-weight': 'bold'})
                                ], style={'text-align': 'center'})
                            ])
                        ], width=3),
                        dbc.Col([
                            dbc.Card([
                                dbc.CardBody([
                                    dcc.Link('Transport & Safety', href='/apps/public_transport', style={'size': '1.5ex', 'font-weight': 'bold'})
                                ], style={'text-align': 'center'})
                            ])
                        ], width=3)                        
                    ], className='row')
                ], width=9),
                dbc.Col([
                    html.Img(src=app.get_asset_url('Logo_PP.png'), style={'height': '180px'})
                ], width=3)
            ]),
        ]),
    ]),
    html.Div(id='page-content', children=[])
])


@app.callback(
    Output('page-content', 'children'),
    [Input('url', 'pathname')]
)
def display_page(pathname):
    if pathname == '/apps/public_transport':
        return public_transport.layout
    if pathname == '/apps/migrations':
        return migrations.layout
    else:
        return migrations.layout


if __name__ == '__main__':
    app.run_server(debug=False)