import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from app import app
from app import server

from apps import public_transport, migrations

app.layout = html.Div([
    html.H1("Barcelona - Urban Analysis", style={'text-align':'left', 'color':'red'}),
    dcc.Location(id='url', refresh=False),
    html.Div([
        dcc.Link('Public Transport', href='/apps/public_transport'),
        dcc.Link('Migrations', href='/apps/migrations')
    ], className='row'),
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