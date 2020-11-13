# YAAA!
# Import required libraries
import base64
import re

#Importaciones de dash
import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
import os
import re
import sqlalchemy
from sqlalchemy import create_engine, text, Table, MetaData, inspect, Column, Integer, String, ForeignKey,DateTime, Numeric
import psycopg2
import psycopg2.extras as extras
import io
import time
from pandas.io.json import json_normalize
import unidecode as uni
from sodapy import Socrata
import dash_table

# Importaciones de los diccionarios
from diccionarios import dpt_dict, mun_dict, diccionario_zoom_center,analysis_var

# Importaciones de la base de datos
import psycopg2
from sqlalchemy import create_engine, text

# Importaciones de back end
import pandas as pd
import json
from flask import Flask

# Cargar geojson de departamentos
with open('departamentos.geojson') as f:
    geojson_departamentos = json.loads(f.read())

# Cargar geojson de municipios

with open('colombia.json') as response:
    geojson_municipios = json.load(response)


# Token de acceso a https://www.mapbox.com/
token = 'pk.eyJ1IjoibmV3dXNlcmZvcmV2ZXIiLCJhIjoiY2o2M3d1dTZiMGZobzMzbnp2Z2NiN3lmdyJ9.cQFKe3F3ovbfxTsM9E0ZSQ'

#Procedimiento para sumar el código del departamento (en formato string) y el código del municipio (en formato string).

param_dic = {
    "host"      : "secop-ds4a-instance.cv1xc7htsshw.sa-east-1.rds.amazonaws.com",
    "database"  : "secopds4a",
    "user"      : "secop_postgres",
    "password"  : "Secopds4a"
}

def connect(params_dic):
    """ Connect to the PostgreSQL database server """
    conn = None
    try:
        # connect to the PostgreSQL server
        print('Connecting to the PostgreSQL database...')
        conn = psycopg2.connect(**params_dic)
    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        sys.exit(1) 
    print("Connection successful")
    return conn
conn = connect(param_dic)

df_master = pd.read_sql('select * from public.tmp_depto', conn)
df_master = df_master[df_master['anno_cargue_secop'] == '2020'][['departamento_entidad', 'cuantia_contrato']].groupby('departamento_entidad').sum('cuantia_contrato').reset_index()
df_master['NOMBRE_DPT'] = df_master['departamento_entidad'].str.upper().apply(lambda x: uni.unidecode(x))
df_master['cuantia_contrato'] = round(df_master['cuantia_contrato']/1000, 2)
df_master = df_master[['NOMBRE_DPT', 'cuantia_contrato']].copy()

# Funcion de filtrado por cluster
def filtrar_cluster(df,cluster_dropdown):
    '''
    Función para filtrar los cluster en la tabla maestra (1122 municipios).
    Recibe un Dataframe y devuelve otro Dataframe filtrado.
    '''
    filtered_df = df[df['NOMBRE_DPT'].isin(cluster_dropdown)]
    return filtered_df

# Funcion de filtrado por cluster
def filtrar_cluster_tabla_positivos(df,cluster_dropdown):
    '''
    Función para filtrar los cluster en la tabla maestra (1122 municipios).
    Recibe un Dataframe y devuelve otro Dataframe filtrado.
    '''
    filtered_df = df[df['cluster_a'].isin(cluster_dropdown)]
    return filtered_df

# Create controls

cluster_options = [{'NOMBRE_DPT':'AMAZONAS','value':'AMAZONAS'},
                   {'NOMBRE_DPT':'ANTIOQUIA','value':'ANTIOQUIA'},
                   {'NOMBRE_DPT':'ARAUCA','value':'ARAUCA'},
                   {'NOMBRE_DPT':'ATLANTICO','value':'ATLANTICO'},
                   {'NOMBRE_DPT':'BOGOTA DC','value':'BOGOTA DC'},
                   {'NOMBRE_DPT':'BOLIVAR','value':'BOLIVAR'},
                   {'NOMBRE_DPT':'BOYACA','value':'BOYACA'},
                   {'NOMBRE_DPT':'CALDAS','value':'CALDAS'},
                   {'NOMBRE_DPT':'CAQUETA','value':'CAQUETA'},
                   {'NOMBRE_DPT':'CASANARE','value':'CASANARE'},
                   {'NOMBRE_DPT':'CAUCA','value':'CAUCA'},
                   {'NOMBRE_DPT':'CESAR','value':'CESAR'},
                   {'NOMBRE_DPT':'CHOCO','value':'CHOCO'},
                   {'NOMBRE_DPT':'CORDOBA','value':'CORDOBA'},
                   {'NOMBRE_DPT':'CUNDINAMARCA','value':'CUNDINAMARCA'},
                   {'NOMBRE_DPT':'GUAINIA','value':'GUAINIA'},
                   {'NOMBRE_DPT':'GUAVIARE','value':'GUAVIARE'},
                   {'NOMBRE_DPT':'HUILA','value':'HUILA'},
                   {'NOMBRE_DPT':'LA GUAJIRA','value':'LA GUAJIRA'},
                   {'NOMBRE_DPT':'MAGDALENA','value':'MAGDALENA'},
                   {'NOMBRE_DPT':'META','value':'META'},
                   {'NOMBRE_DPT':'NARIÑO','value':'NARIÑO'},
                   {'NOMBRE_DPT':'NORTE DE SANTANDER','value':'NORTE DE SANTANDER'},
                   {'NOMBRE_DPT':'PUTUMAYO','value':'PUTUMAYO'},
                   {'NOMBRE_DPT':'QUINDIO','value':'QUINDIO'},
                   {'NOMBRE_DPT':'RISARALDA','value':'RISARALDA'},
                   {'NOMBRE_DPT':'SAN ANDRES PROVIDENCIA Y SANTA CATALINA','value':'SAN ANDRES, PROVIDENCIA Y SANTA CATALINA'},
                   {'NOMBRE_DPT':'SANTANDER','value':'SANTANDER'},
                   {'NOMBRE_DPT':'SUCRE','value':'SUCRE'},
                   {'NOMBRE_DPT':'TOLIMA','value':'TOLIMA'},
                   {'NOMBRE_DPT':'VALLE DEL CAUCA','value':'VALLE DEL CAUCA'},
                   {'NOMBRE_DPT':'VAUPES','value':'VAUPES'},
                   {'NOMBRE_DPT':'VICHADA','value':'VICHADA'}
]



dict_categories = {'remuneracion':['remuneracion_p_remunerado', 'remuneracion_p_no_remunerado',
       'remuneracion_p_indeterminado'],'escolaridad':['escolaridad_p_no_escolaridad',
       'escolaridad_p_basico', 'escolaridad_p_avanzado',
       'escolaridad_p_indeterminado'],'salud':['salud_p_atencion_formal', 'salud_p_atencion_no_formal',
       'salud_p_atencion_indeterminado'],'pareja':['pareja_p_si', 'pareja_p_no',
       'pareja_p_indeterminado'],'hijos':['hijos_p_0', 'hijos_p_1', 'hijos_p_2',
       'hijos_p_3_o_mas'],'inmigracion_1':['inmigracion1_p_no',
       'inmigracion1_p_si', 'inmigracion1_p_indeterminado'],'inmigracion_5':['inmigracion5_p_no',
       'inmigracion5_p_si', 'inmigracion5_p_indeterminado']}

list_categories_alone = ['remuneracion_p_remunerado', 'remuneracion_p_no_remunerado','remuneracion_p_indeterminado','escolaridad_p_no_escolaridad','escolaridad_p_basico',
'escolaridad_p_avanzado','escolaridad_p_indeterminado','salud_p_atencion_formal', 'salud_p_atencion_no_formal','salud_p_atencion_indeterminado','pareja_p_si', 'pareja_p_no',
'pareja_p_indeterminado','hijos_p_0', 'hijos_p_1', 'hijos_p_2','hijos_p_3_o_mas','inmigracion1_p_no','inmigracion1_p_si', 'inmigracion1_p_indeterminado','inmigracion5_p_no',
'inmigracion5_p_si', 'inmigracion5_p_indeterminado']

lista_columnas_analisis = ['alfabetizacion','analfabetismo','escolarizado', 'descolarizado', 'remunerado','no_remunerado', 'atencion_formal', 'atencion_informal','no_necesita_atencion']
analysis_options = [{'label': i.title(),'value': i } for i in lista_columnas_analisis]
lista_line_analysis_options = ['p_escolarizacion', 'p_atencion_salud_formal', 'p_trabajo_remunerado']
line_analysis_options = [{'label': i.title(),'value': i } for i in lista_line_analysis_options]
lista_prueba = [{'label':'Escolarización','value':'p_escolarizacion'},{'label':'Atención Salud','value':'p_atencion_salud_formal'},{'label':'Trabajo Remunerado','value':'p_trabajo_remunerado'}]
lista_barras_drop_prueba = [{'label' : i.title() ,'value' : i} for i in dict_categories]
lista_line_plot = [{'label': re.sub(r'_\w_',': ',i).title(),'value': i } for i in list_categories_alone]


#Decoración del Frontend
test_png = 'Team_86_Logo.png' # Logo Team_86
test_base64 = base64.b64encode(open(test_png, 'rb').read()).decode('ascii')
ds4a_png = 'Secop I.png' # Logo DS4A
ds4a_base64 = base64.b64encode(open(ds4a_png, 'rb').read()).decode('ascii')
#min_png = 'mintic.png' # Logo DS4A
#min_base64 = base64.b64encode(open(min_png, 'rb').read()).decode('ascii')

#Carga de datos
df_line_plot = pd.read_csv('quantity_by_cluster.csv', sep = ';')
df_line_plot = df_line_plot.sort_values(by = 'edad')
df_all = pd.read_csv('cs_general2.csv',sep = ',')
df_all = df_all.sort_values(by = 'edad')


app = dash.Dash(__name__)
server = app.server


# Create app layout
app.layout = html.Div(
    [
        dcc.Store(id='aggregate_data'),
        html.Div(
            [
                html.Div(
                    [
                        html.H2(
                            'Colombia Inequality 🇨🇴',

                        ),
                    ],

                    className='eight columns'
                ),
                html.Img(
                    src='data:image/png;base64,{}'.format(test_base64),
                    className='two columns',
                ),
                html.Img(
                    src='data:image/png;base64,{}'.format(ds4a_base64),
                    className='two columns',
                ),
                '''
                html.Img(
                    src='data:image/png;base64,{}'.format(min_base64),
                    className='two columns',
                ),'''
            ],
            id="header",
            className='row',
        ),
        html.Div(
            [
                html.Div(
                    [
                        html.P(
                            'Filter by department:',
                            className="control_label"
                        ),
                        dcc.RadioItems(
                            id='cluster_button_selector',
                            options=[
                                {'label': 'All ', 'value': 'all'},
                                {'label': 'Customize ', 'value': 'custom'}
                            ],
                            value='all',
                            labelStyle={'display': 'inline-block'},
                            className="dcc_control"
                        ),
                        dcc.Dropdown(
                            id='cluster_dropdown_options',
                            options=cluster_options,
                            multi=True,
                            value= [],
                            className="dcc_control"
                        ),
                        dcc.RadioItems(
                            id='group_button_selector',
                            options=[
                                {'label': 'Clustered ', 'value': 'clustered'},
                                {'label': 'Municipality ', 'value': 'municipality'}
                            ],
                            value='clustered',
                            labelStyle={'display': 'inline-block'},
                            className="dcc_control"
                        ),
                        html.P(
                            'Filter by welfare variable:',
                            className="control_label"
                        ),
                        dcc.Dropdown(
                            id='analysis_dropdown_options',
                            options=analysis_options,
                            multi=False,
                            value=[],
                            className="dcc_control"
                        ),
                        html.P(
                            'Select Scatter Plot options:',
                            className="control_label"
                        ),
                        dcc.Dropdown(
                            id='scatter1_dropdown_options',
                            options=analysis_options,
                            multi=False,
                            value=[],
                            className="dcc_control"
                        ),
                        dcc.Dropdown(
                            id='scatter2_dropdown_options',
                            options=analysis_options,
                            multi=False,
                            value=[],
                            className="dcc_control"
                        ),
                        html.P(
                            'Select Top:',
                            className="control_label"
                        ),
                        dcc.RadioItems(
                            id='top_button_selector',
                            options=[
                                {'label': 'Highest 5 ', 'value': 'high_5'},
                                {'label': 'Lowest 5 ', 'value': 'low_5'}
                            ],
                            value='high_5',
                            labelStyle={'display': 'inline-block'},
                            className="dcc_control"
                        ),
                        html.P(
                            'Select Line plot Variable:',
                            className="control_label"
                        ),
                        dcc.Dropdown(
                            id='lineplot_analysis_dropdown_options',
                            options=lista_line_plot,
                            multi=False,
                            value=[],
                            className="dcc_control"
                        ),
                        html.P(
                            'Select Variable through all clusters:',
                            className="control_label"
                        ),
                        dcc.Dropdown(
                            id='barras_dropdown_options',
                            options=lista_barras_drop_prueba,
                            multi=False,
                            value=[],
                            className="dcc_control"
                        ),
                        html.P(
                            'Select Age range:',
                            className="control_label"
                        ),
                    ],
                    className="pretty_container four columns"
                ),
                html.Div(
                    [
                        html.Div(
                            [
                                html.Div(
                                    [
                                        html.P("Women"),
                                        html.H6(
                                            id="women_text",
                                            className="info_text"
                                        )
                                    ],
                                    id="women_percetage",
                                    className="pretty_container",
                                ),

                                html.Div(
                                    [
                                        html.Div(
                                            [
                                                html.P("Men"),
                                                html.H6(
                                                    id="men_text",
                                                    className="info_text"
                                                )
                                            ],
                                            id="men_percentage",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P("Variable",
                                                    id='variable_text'),
                                                html.H6(
                                                    id="variable_percentage_text",
                                                    className="info_text"
                                                )
                                            ],
                                            id="women_percentage",
                                            className="pretty_container"
                                        ),
                                        html.Div(
                                            [
                                                html.P("Municipalities Count"),
                                                html.H6(
                                                    id="municipalities_text",
                                                    className="info_text"
                                                )
                                            ],
                                            id="municipalities_count",
                                            className="pretty_container"
                                        ),
                                    ],
                                    id="tripleContainer",
                                )

                            ],
                            id="infoContainer",
                            className="row"
                        ),
                        html.Div(
                            [
                                dcc.Graph(
                            id='map-plot-municipios',
                            figure={ 
                                'data': [go.Choroplethmapbox(
                                    geojson=geojson_municipios,
                                    locations=df_master['NOMBRE_DPT'], # Esto debería coincidir con el "id" en el geojson
                                    z=df_master['cuantia_contrato'], # Métrica (lo que se va a medir)
                                    colorscale=[
                                                [0,    "blue"],
                                                [0.20, "blue"],
                                                [0.20, "orange"],
                                                [0.40, "orange"],
                                                [0.40, "green"],
                                                [0.60, "green"],
                                                [0.60, "red"],
                                                [0.80, "red"],
                                                [0.80, "rgb(73,33,109)"],
                                                [1,    "rgb(73,33,109)"]], #Colores del degradé del mapa: Cividis, Viridis, Magma 
                                    text=df_master['NOMBRE_DPT'],
                                    featureidkey="properties.NOMBRE_DPT",
                                    colorbar=
                                    {
                                      'title':'Clúster', #Título de la barra de colores
                                      'thickness':10,
                                      'xpad': 5,
                                      'tickvals' : [0,1,2,3,4]
                                    },
                                    marker=
                                    { # Atributos de los polígonos
                                    'opacity':0.5, #Transparencia de los polígonos
                                    'line': # Atributos de las líneas
                                      {
                                      'width':1, # Grosor de la línea frontera de los polígonos
                                      'color':'#999' # Color de la línea
                                      }
                                    },
                                    hovertemplate = '<b>%{text}</b> <br>Clúster: %{z:,.d}<extra></extra>' # Override de hoverinfo
                                )],
                                'layout': go.Layout(
                                        mapbox_style="light", #streets, dark, light, outdoors, satellite, satellite-streets, carto-positron
                                        autosize=False,
                                        mapbox_accesstoken=token,
                                        mapbox_zoom=4.5,
                                        uirevision= 'no reset of zoom', #Sirve para que el zoom no se actualice
                                        margin={'t': 0, 'l': 0, 'r': 0, 'b': 0, 'pad':0},
                                        mapbox_center={"lat": 4.5709, "lon": -74.2973},
                                        height = 650
                                    )
                            }
                        )
                            ],
                            id="div-map-departamentos",
                            className="pretty_container"
                        ),
                    ],
                    id="rightCol",
                    className="eight columns"
                )
            ],
            className="row"
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='bar_graph_cluster'),
                    ],
                    className='pretty_container seven columns',
                ),
                html.Div(
                    [
                        dcc.Graph(id='scatter_plot'),
                    ],
                    className='pretty_container five columns',
                ),
            ],
            className='row'
        ),
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='line-plot')
                    ],
                    className='pretty_container seven columns',
                ),
                html.Div(
                    [
                        dcc.Graph(id='bar_graph')
                    ],
                    className='pretty_container five columns',
                ),
            ],
            className='row'
        ),
        
        #html.Div(
         #   [
         #       html.Div(
         #           [
         #               dcc.Graph(id='line-plot')
         #           ],
         #           className='pretty_container seven columns',
         #       )
         #   ],
         #   className='row'
        #),
        
        html.Div(
            [
                html.Div(
                    [
                        dcc.Graph(id='bars-cluster')
                    ],
                    className='pretty_container',
                )
            ],
            #className='row'
        ),
    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)


@app.callback(
        Output('cluster_dropdown_options','value'),
    [
        Input('cluster_button_selector', 'value')
    ]
)
def update_dropdown(radio_button):
    if radio_button == 'all':
        filtered_list = ['0','1','2','3','4']
        return filtered_list
    else:
        return []


@app.callback(
   [
        Output('municipalities_text', 'children'),
        Output('variable_percentage_text','children'), #Cambia
        Output('variable_text','children'),
        Output('women_text','children'), #Cambia
        Output('men_text','children') #Cambia
   ],
   [
        Input('map-plot-municipios', 'clickData'),# Esta es para cuando se le da click al municipio (hoverData para pasarlo por encima)
        Input('cluster_dropdown_options','value'),
        Input('analysis_dropdown_options','value'),
        Input('group_button_selector','value')
   ]
)
def update_text_boxes(map_data,cluster_dropdown,analysis_dropdown_options,group_button):
    if group_button == 'clustered':
        filtered_df = filtrar_cluster(df_master,cluster_dropdown)
        percentage_men = filtered_df['sexo_m'].sum()/filtered_df['poblacion'].sum()
        percentage_women = filtered_df['sexo_f'].sum()/filtered_df['poblacion'].sum()
        return [filtered_df.shape[0],
                r'{:.2%}'.format(filtered_df[analysis_dropdown_options].mean()),
                analysis_dropdown_options.title(),
                r'{:.2%}'.format((percentage_women)),
                r'{:.2%}'.format((percentage_men))]
    elif group_button == 'municipality':
        filtered_df = filtrar_cluster(df_master,cluster_dropdown)
        municipio = [each['location'] for each in map_data['points']] if map_data else None
        filtered_df_sex = df_master[df_master['str_dpto_mpio'] == municipio[0]]
        percentage_men = filtered_df_sex['sexo_m']/(filtered_df_sex['sexo_m'] + filtered_df_sex['sexo_f'])
        percentage_women = filtered_df_sex['sexo_f']/(filtered_df_sex['sexo_m'] + filtered_df_sex['sexo_f'])
        analysis_var_mun = filtered_df[filtered_df['str_dpto_mpio'] == municipio[0]][analysis_dropdown_options]
        return [filtered_df.shape[0],
                r'{:.2%}'.format(analysis_var_mun.values[0]),
                analysis_dropdown_options.title(),
                r'{:.2%}'.format((percentage_women.values[0])),
                r'{:.2%}'.format((percentage_men.values[0]))]


@app.callback(
    [
    Output('map-plot-municipios','figure')
    ],
    [
    Input('cluster_dropdown_options','value')
    ]
)
def update_map(cluster_dropdown):
    filtered_df = filtrar_cluster(df_master,cluster_dropdown)
    text = filtered_df['municipio'] + ',' + filtered_df['departamento'] + '.' + filtered_df['poblacion'].apply(lambda x : 'Población: ' + str(f'{x:,}'))
    return [{ 
            'data': [go.Choroplethmapbox(
                                    geojson=geojson_municipios,
                                    locations=filtered_df['str_dpto_mpio'], # Esto debería coincidir con el "id" en el geojson
                                    z=filtered_df['labels'], # Métrica (lo que se va a medir)
                                    colorscale= [
                                                [0,    "blue"],
                                                [0.20, "blue"],
                                                [0.20, "orange"],
                                                [0.40, "orange"],
                                                [0.40, "green"],
                                                [0.60, "green"],
                                                [0.60, "red"],
                                                [0.80, "red"],
                                                [0.80, "rgb(73,33,109)"],
                                                [1,    "rgb(73,33,109)"]], #Colores del degradé del mapa: Cividis, Viridis, Magma 
                                    text=text,
                                    colorbar=
                                    {
                                      'title':'Clúster', #Título de la barra de colores
                                      'thickness':10,
                                      'xpad': 5,
                                      'tickvals' : [0,1,2,3,4]
                                    },
                                    marker=
                                    { # Atributos de los polígonos
                                    'opacity':0.5, #Transparencia de los polígonos
                                    'line': # Atributos de las líneas
                                      {
                                      'width':1, # Grosor de la línea frontera de los polígonos
                                      'color':'#999' # Color de la línea
                                      }
                                    },
                                    hovertemplate = '<b>%{text}</b> <br>Clúster: %{z:,.d}<extra></extra>' # Override de hoverinfo
                                )],
                                'layout': go.Layout(
                                        mapbox_style="light", #streets, dark, light, outdoors, satellite, satellite-streets, carto-positron
                                        autosize=False,
                                        mapbox_accesstoken=token,
                                        mapbox_zoom=4.5,
                                        uirevision= 'no reset of zoom', #Sirve para que el zoom no se actualice
                                        margin={'t': 0, 'l': 0, 'r': 0, 'b': 0, 'pad':0},
                                        mapbox_center={"lat": 4.5709, "lon": -74.2973},
                                        height = 650
                                    )
                            }]

@app.callback(
    [
    Output('bar_graph','figure')
    ],
    [
    Input('cluster_dropdown_options','value'),
    Input('analysis_dropdown_options','value'),
    Input('top_button_selector','value')
    ]
)
def update_barplot(cluster_dropdown,analysis_dropdown_options,top_button_selector):
    if top_button_selector == 'high_5':
        filtered_df = filtrar_cluster(df_master,cluster_dropdown)
        df_cluster0 = filtered_df[filtered_df['labels'] == 0].sort_values(by = analysis_dropdown_options, ascending = False)[0:7]
        df_cluster1 = filtered_df[filtered_df['labels'] == 1].sort_values(by = analysis_dropdown_options, ascending = False)[0:7]
        df_cluster2 = filtered_df[filtered_df['labels'] == 2].sort_values(by = analysis_dropdown_options, ascending = False)[0:7]
        df_cluster3 = filtered_df[filtered_df['labels'] == 3].sort_values(by = analysis_dropdown_options, ascending = False)[0:7]
        df_cluster4 = filtered_df[filtered_df['labels'] == 4].sort_values(by = analysis_dropdown_options, ascending = False)[0:7]
        return [{'data': [
                        {'x': df_cluster0['municipio'], 'y': df_cluster0[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 0','opacity' : 0.9},
                        {'x': df_cluster1['municipio'], 'y': df_cluster1[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 1','opacity' : 0.9},
                        {'x': df_cluster2['municipio'], 'y': df_cluster2[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 2','opacity' : 0.9},
                        {'x': df_cluster3['municipio'], 'y': df_cluster3[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 3','opacity' : 0.9},
                        {'x': df_cluster4['municipio'], 'y': df_cluster4[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 4','opacity' : 0.9}
                        ],
                        'layout': {
                        'title': analysis_dropdown_options.title() + ' Highest 5',
                        'xaxis': {'title' : 'Municipality'},
                        'yaxis': {'title' : 'Percentage'}}
                }]
    else:
        filtered_df = filtrar_cluster(df_master,cluster_dropdown)
        df_cluster0 = filtered_df[filtered_df['labels'] == 0].sort_values(by = analysis_dropdown_options, ascending = True)[0:7]
        df_cluster1 = filtered_df[filtered_df['labels'] == 1].sort_values(by = analysis_dropdown_options, ascending = True)[0:7]
        df_cluster2 = filtered_df[filtered_df['labels'] == 2].sort_values(by = analysis_dropdown_options, ascending = True)[0:7]
        df_cluster3 = filtered_df[filtered_df['labels'] == 3].sort_values(by = analysis_dropdown_options, ascending = True)[0:7]
        df_cluster4 = filtered_df[filtered_df['labels'] == 4].sort_values(by = analysis_dropdown_options, ascending = True)[0:7]
        return [{'data':[
                        {'x': df_cluster0['municipio'], 'y': df_cluster0[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 0','opacity' : 0.9},
                        {'x': df_cluster1['municipio'], 'y': df_cluster1[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 1','opacity' : 0.9},
                        {'x': df_cluster2['municipio'], 'y': df_cluster2[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 2','opacity' : 0.9},
                        {'x': df_cluster3['municipio'], 'y': df_cluster3[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 3','opacity' : 0.9},
                        {'x': df_cluster4['municipio'], 'y': df_cluster4[analysis_dropdown_options], 'type': 'bar', 'name': 'Clúster 4','opacity' : 0.9}
                        ],
                        'layout': {
                        'title': analysis_dropdown_options.title() + ' Lowest 5',
                        'xaxis': {'title' : 'Municipality'},
                        'yaxis': {'title' : 'Percentage'}}
                }]


@app.callback(
    [
    Output('scatter_plot','figure')
    ],
    [
    Input('cluster_dropdown_options','value'),
    Input('analysis_dropdown_options','value'),
    Input('scatter1_dropdown_options','value'),
    Input('scatter2_dropdown_options','value')
    ]
)
def update_scatterplot(cluster_dropdown,analysis_dropdown_options,scatter1_dropdown_options, scatter2_dropdown_options):
    filtered_df = filtrar_cluster(df_master,cluster_dropdown)
    return [
            {
            'data': [
                dict(
                    x=filtered_df[filtered_df['labels'] == i][scatter1_dropdown_options],
                    y=filtered_df[filtered_df['labels'] == i][scatter2_dropdown_options],
                    text=filtered_df[filtered_df['labels'] == i]['municipio'],
                    mode='markers',
                    opacity=0.7,
                    marker={
                        'size': 15,
                        'line': {'width': 0.5, 'color': 'white'}
                    },
                    name = 'Clúster ' + str(i)
                ) for i in sorted(filtered_df.labels.unique())
            ],
            'layout': dict(
                xaxis={'title': scatter1_dropdown_options.title()},
                yaxis={'title': scatter2_dropdown_options.title()},
                margin={'l': 40, 'b': 40, 't': 25, 'r': 10},
                legend={'x': 0, 'y': 1},
                hovermode='closest',
                title = scatter1_dropdown_options.title() + ' vs ' + scatter2_dropdown_options.title()
            ),
        }]



@app.callback(
    [
    Output('bar_graph_cluster','figure')
    ],
    [
    Input('cluster_dropdown_options','value')
    ]
)
def update_barplot_cluster(cluster_dropdown):
    filtered_df = filtrar_cluster(df_master,cluster_dropdown)
    df_cluster0 = filtered_df[filtered_df['labels'] == 0].describe().loc['mean',lista_columnas_analisis]
    df_cluster1 = filtered_df[filtered_df['labels'] == 1].describe().loc['mean',lista_columnas_analisis]
    df_cluster2 = filtered_df[filtered_df['labels'] == 2].describe().loc['mean',lista_columnas_analisis]
    df_cluster3 = filtered_df[filtered_df['labels'] == 3].describe().loc['mean',lista_columnas_analisis]
    df_cluster4 = filtered_df[filtered_df['labels'] == 4].describe().loc['mean',lista_columnas_analisis]
    return [{'data':[
                    {'x': df_cluster0.index, 'y': df_cluster0.values, 'type': 'bar', 'name': 'Clúster 0','opacity' : 0.9},
                    {'x': df_cluster1.index, 'y': df_cluster1.values, 'type': 'bar', 'name': 'Clúster 1','opacity' : 0.9},
                    {'x': df_cluster2.index, 'y': df_cluster2.values, 'type': 'bar', 'name': 'Clúster 2','opacity' : 0.9},
                    {'x': df_cluster2.index, 'y': df_cluster3.values, 'type': 'bar', 'name': 'Clúster 3','opacity' : 0.9},
                    {'x': df_cluster2.index, 'y': df_cluster4.values, 'type': 'bar', 'name': 'Clúster 4','opacity' : 0.9}
                    ],
                        'layout': {
                        'title': 'Clúster Variables',
                        'xaxis': {'title' : 'Variable'},
                        'yaxis': {'title' : 'Percentage'}}
                }]
    
@app.callback(
    [
    Output('line-plot','figure')
    ],
    [
    Input('cluster_dropdown_options','value'),
    Input('lineplot_analysis_dropdown_options','value')
    ]
)
def update_lineplot(cluster_dropdown, lineplot_analysis_dropdown_options):
    filtered_df = filtrar_cluster_tabla_positivos(df_all,cluster_dropdown)
    filtered_df_m = filtered_df[filtered_df['sexo'] == 'H'].groupby(by = 'edad').mean()
    filtered_df_f = filtered_df[filtered_df['sexo'] == 'M'].groupby(by = 'edad').mean()
    title = re.sub(r'_\w_',': ',lineplot_analysis_dropdown_options).title()
    title = re.sub(r'_',' ',title)
    layout = go.Layout(
        title = title
    )
    fig = go.Figure(layout = layout)
    fig.add_trace(go.Scatter(x = filtered_df_m.index, y = filtered_df_m[lineplot_analysis_dropdown_options],
                    mode='lines',
                    name='Men'))
    fig.add_trace(go.Scatter(x = filtered_df_f.index, y = filtered_df_f[lineplot_analysis_dropdown_options],
                    mode='lines',
                    name='Women'))
    fig.update_xaxes(title_text='Age (DANE Range)')
    fig.update_yaxes(title_text='Percentage')
    
    
    return [fig]


@app.callback(
    [
    Output('bars-cluster','figure')
    ],
    [
    Input('cluster_dropdown_options','value'),
    Input('barras_dropdown_options','value'),
    Input('age_dropdown_options','value')
    ]
)
def update_bars_cluster(cluster_dropdown,barras_dropdown_options,age_dropdown_options):
    filtered_df = filtrar_cluster_tabla_positivos(df_all,cluster_dropdown)
    filtered_df = filtered_df[filtered_df['edad'].isin(age_dropdown_options)]
    if barras_dropdown_options == 'remuneracion':
        lista_variables = dict_categories['remuneracion']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    elif barras_dropdown_options == 'escolaridad':
        lista_variables = dict_categories['escolaridad']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    elif barras_dropdown_options == 'salud':
        lista_variables = dict_categories['salud']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    elif barras_dropdown_options == 'pareja':
        lista_variables = dict_categories['pareja']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    elif barras_dropdown_options == 'hijos':
        lista_variables = dict_categories['hijos']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    elif barras_dropdown_options == 'inmigracion_1':
        lista_variables = dict_categories['inmigracion_1']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]
    else:
        lista_variables = dict_categories['inmigracion_5']
        lista_variables_x = [re.sub(r'.+_\w_+','',i).title() for i in lista_variables]

    df_cluster0 = filtered_df[filtered_df['cluster_a'] == 0]
    df_0_h = df_cluster0.groupby(['sexo','edad']).mean()[lista_variables].loc['H'].mean()
    df_0_m = df_cluster0.groupby(['sexo','edad']).mean()[lista_variables].loc['M'].mean()
    df_cluster1 = filtered_df[filtered_df['cluster_a'] == 1]
    df_1_h = df_cluster1.groupby(['sexo','edad']).mean()[lista_variables].loc['H'].mean()
    df_1_m = df_cluster1.groupby(['sexo','edad']).mean()[lista_variables].loc['M'].mean()
    df_cluster2 = filtered_df[filtered_df['cluster_a'] == 2]
    df_2_h = df_cluster2.groupby(['sexo','edad']).mean()[lista_variables].loc['H'].mean()
    df_2_m = df_cluster2.groupby(['sexo','edad']).mean()[lista_variables].loc['M'].mean()
    df_cluster3 = filtered_df[filtered_df['cluster_a'] == 3]
    df_3_h = df_cluster3.groupby(['sexo','edad']).mean()[lista_variables].loc['H'].mean()
    df_3_m = df_cluster3.groupby(['sexo','edad']).mean()[lista_variables].loc['M'].mean()
    df_cluster4 = filtered_df[filtered_df['cluster_a'] == 4]
    df_4_h = df_cluster4.groupby(['sexo','edad']).mean()[lista_variables].loc['H'].mean()
    df_4_m = df_cluster4.groupby(['sexo','edad']).mean()[lista_variables].loc['M'].mean()
    string = ''
    return [{
            'data': [
                {'x': lista_variables_x, 'y': list(df_0_h.values), 'type': 'bar','name':'Men','xaxis':'x1','legendgroup':'Men','marker':{'color':'blue'}},
                {'x': lista_variables_x, 'y': list(df_0_m.values), 'type': 'bar','name':'Women','xaxis' : 'x1','legendgroup':'Women','marker':{'color':'pink'}},
                {'x': lista_variables_x, 'y': list(df_1_h.values), 'type': 'bar','xaxis':'x2','name':'Men','showlegend' : False,'legendgroup':'Men','marker':{'color':'blue'}},
                {'x': lista_variables_x, 'y': list(df_1_m.values), 'type': 'bar','xaxis':'x2','name':'Women','showlegend': False,'legendgroup':'Women','marker':{'color':'pink'}},
                {'x': lista_variables_x, 'y': list(df_2_h.values), 'type': 'bar','xaxis':'x3','name':'Men','showlegend' : False,'legendgroup':'Men','marker':{'color':'blue'}},
                {'x': lista_variables_x, 'y': list(df_2_m.values), 'type': 'bar','xaxis':'x3','name':'Women','showlegend': False,'legendgroup':'Women','marker':{'color':'pink'}},
                {'x': lista_variables_x, 'y': list(df_3_h.values), 'type': 'bar','xaxis':'x4','name':'Men','showlegend' : False,'legendgroup':'Men','marker':{'color':'blue'}},
                {'x': lista_variables_x, 'y': list(df_3_m.values), 'type': 'bar','xaxis':'x4','name':'Women','showlegend': False,'legendgroup':'Women','marker':{'color':'pink'}},
                {'x': lista_variables_x, 'y': list(df_4_h.values), 'type': 'bar','xaxis':'x5','name':'Men','showlegend' : False,'legendgroup':'Men','marker':{'color':'blue'}},
                {'x': lista_variables_x, 'y': list(df_4_m.values), 'type': 'bar','xaxis':'x5','name':'Women','showlegend': False,'legendgroup':'Women','marker':{'color':'pink'}},
            ],
            'layout': {
                'title' : barras_dropdown_options.title() + ' (Age Range: ' + string.join(['-' + str(i) + '-' for i in age_dropdown_options]) + ' )',
                'yaxis' : {'title' : 'Percentage'},
                'xaxis' : {'domain':[0, 0.18],'title':'Cluster 0'},
                'xaxis2': {'domain':[0.2, 0.38],'title':'Cluster 1'},
                'xaxis3': {'domain':[0.4,0.58],'title':'Cluster 2'},
                'xaxis4': {'domain':[0.6, 0.78],'title':'Cluster 3'},
                'xaxis5': {'domain':[0.8,0.98],'title':'Cluster 4'},
            },
        }]
# Main
#if __name__ == '__main__':
 #   app.server.run(debug=True, threaded=False, port = 5011)
    #app.server.run(debug=False, threaded=True, port = 5011, host = 'ec2-54-201-96-238.us-west-2.compute.amazonaws.com')
if __name__ == "__main__":
        app.run_server(host="0.0.0.0", port="8050", debug=True)
