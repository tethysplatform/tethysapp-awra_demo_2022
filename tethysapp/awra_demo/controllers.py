import datetime as dt
import os
import json

import pandas as pd
import geopandas as gpd
import numpy as np
import scipy.stats as sp
import scipy.optimize as op
from tethys_sdk.layouts import MapLayout
from tethys_sdk.routing import controller

from .app import AwraDemo as app


@controller(
    name='map',
    app_workspace=True,
)
class AwraMapLayout(MapLayout):
    app = app
    initial_map_extent = [-112.1, 38, -111, 41]
    min_zoom = 2
    max_zoom = 15
    map_title = 'AWRA Map'
    map_subtitle = 'NWIS Sites'
    plot_slide_sheet = True
    show_properties_popup = True

    def compose_layers(self, request, map_view, app_workspace, *args, **kwargs):
        # Import Data
        sites_path = os.path.join(app_workspace.path, 'USGS_Site_Info.geojson')

        with open(sites_path, 'r') as f:
            site_json = json.loads(f.read())

        # Create GeoJSON Layer
        sites_layer = self.build_geojson_layer(
            geojson=site_json,
            layer_name='nwis-sites',
            layer_title='NWIS Sites',
            layer_variable='reference',
            selectable=True,
            visible=True,
            extent=self.initial_map_extent,
            plottable=True,
        )

        # Create Layer Groups
        layer_groups = [
            self.build_layer_group(
                id='nwis-layers',
                display_name='Gages',
                layer_control='radio',
                layers=[sites_layer],
            ),           
        ]

        return layer_groups

    def get_plot_for_layer_feature(self, request, layer_name, feature_id, app_workspace):
        """
        Retrieves plot data for given feature on given layer.
        Args:
            layer_name (str): Name/id of layer.
            feature_id (str): ID of feature.
        Returns:
            str, list<dict>, dict: plot title, data series, and layout options, respectively.
        """
        # Import data
        data_path = os.path.join(app_workspace.path, 'USGS_Site_Data.csv')
        USGS_Site_Data = pd.read_csv(data_path, low_memory=False, index_col='dates')
        
        site_no = feature_id
        prob1, discharge1 = fdc(USGS_Site_Data, site_no, 1900, 2020)
        prob2, discharge2 = fdc(USGS_Site_Data, site_no, 1900, 1970)
        prob3, discharge3 = fdc(USGS_Site_Data, site_no, 1970, 2020)
        
        series1 = dict(x=prob1, y=discharge1, name=f'{site_no} 1900-2020')
        series2 = dict(x=prob2, y=discharge2, name=f'{site_no} 1900-1970')
        series3 = dict(x=prob3, y=discharge3, name=f'{site_no} 1970-2020')
        
        layout = {
            'xaxis': {
                'title': 'probability',
                'dtick': 0.05
            },
            'yaxis': {
                'title': 'discharge (cfs)',
                'type': 'log'
            }
        }
        
        data = [series1, series2, series3]
        
        return f'Flow Duration Curve for {site_no}', data, layout


def fdc(df, site, begyear=1900, endyear=2022, normalizer=1):
    '''
    Generate flow duration curve for hydrologic time series data
    
    PARAMETERS:
        df = pandas dataframe of interest; must have a date or date-time as the index
        site = pandas column containing discharge data; must be within df
        begyear = beginning year of analysis; defaults to 1900
        endyear = end year of analysis; defaults to 2022
        normalizer = value to use to normalize discharge; defaults to 1 (no normalization)
    
    RETURNS:
        probability, discharge
        
    REQUIRES:
        numpy as np
        pandas as pd
        matplotlib.pyplot as plt
        scipy.stats as sp
    '''
    # limit dataframe to only the site
    df = df[[site]]
    
    # filter dataframe to only include dates of interest
    dt_index = pd.to_datetime(df.index)
    df.index = dt_index
    data = df[(dt_index > dt.datetime(begyear, 1, 1))&(dt_index < dt.datetime(endyear, 1, 1))]

    # remove na values from dataframe
    data = data.dropna()

    # take average of each day of year (from 1 to 366) over the selected period of record
    data['doy'] = data.index.dayofyear
    dailyavg = data[site].groupby(data['doy']).mean()
        
    data = np.sort(dailyavg)

    ## uncomment the following to use normalized discharge instead of discharge
    #mean = np.mean(data)
    #std = np.std(data)
    #data = [(data[i]-np.mean(data))/np.std(data) for i in range(len(data))]
    data = [(data[i])/normalizer for i in range(len(data))]
    
    # ranks data from smallest to largest
    ranks = sp.rankdata(data, method='average')

    # reverses rank order
    ranks = ranks[::-1]
    
    # calculate probability of each rank
    prob = [(ranks[i]/(len(data)+1)) for i in range(len(data)) ]
    
    return prob, data
