# -*- coding: utf-8 -*-
"""hyperparameter tunning for facebook.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1nLmYJiO2-BLyNdy9oO8C6wugv5eq_nSH
"""

!pip install pmdarima

!pip install yfinance

import yfinance
import pandas as pd
from sklearn.metrics import mean_squared_error
from sklearn.metrics import mean_absolute_error
from fbprophet import Prophet
import pandas as pd
#from pmdarima.arima import auto_arima
from statsmodels.tsa.holtwinters import ExponentialSmoothing


import numpy as np
import pmdarima as pm
from pmdarima import pipeline
from pmdarima import model_selection
from pmdarima import preprocessing as ppc
from pmdarima import arima
from matplotlib import pyplot as plt

"""Para obtener los precios de cierre de los índices SP500, FTSE, DAX y NIKKEI, especificar los nombres, la fecha de inicio y fin, y el intervalo (diario=1d):"""

raw_data = yfinance.download (tickers = "^GSPC ^FTSE ^N225 ^GDAXI", start = "2020-10-01", 
                              end = "2020-11-13", interval = "1d", group_by = 'ticker', auto_adjust = True, treads = True)

raw_data.tail()

df_comp=raw_data.copy()

"""Para cada día y cada precio obtenemos 4 datos, los precios de: apertura, máximo, bajo, cierre y volumen. Queremos los precios de cierre así que seleccionamos sólo la variable cierre para cada precio, los guardamos en 4 nuevas variables en el dataset y les ponemos los nombres del indice al que corresponden."""

df_comp['spx'] = df_comp['^GSPC'].Close[:]
df_comp['dax'] = df_comp['^GDAXI'].Close[:]
df_comp['ftse'] = df_comp['^FTSE'].Close[:]
df_comp['nikkei'] = df_comp['^N225'].Close[:]

df_comp.head()

"""Pre-procesado: eliminar las variables que sobran, arreglar la frecuencia a business days y rellenar datos faltantes."""

df_comp = df_comp.iloc[1:]
del df_comp['^N225']
del df_comp['^GSPC']
del df_comp['^GDAXI']
del df_comp['^FTSE']
df_comp=df_comp.asfreq('b')
df_comp=df_comp.fillna(method='ffill')
df_comp.reset_index(inplace=True)

df_comp.columns = ['Date', 'spx', 'dax', 'ftse', 'nikkei']
#df_comp.set_index('Date', inplace=True)

df=pd.melt(df_comp, id_vars=['Date'])
df.columns = ['ds', 'variable', 'y']
df

df=df[df['variable']=='spx']

df.drop('variable', axis=1, inplace=True)

df.head()

def holidays():
    especial = pd.DataFrame({
    'holiday': 'especial',
    'ds': pd.to_datetime([
                            '2019-01-01', '2019-12-25', 
                            '2020-01-01', '2020-12-25'
                            ]),
    'lower_window': 0,
    'upper_window': 0,
    })

    alta = pd.DataFrame({
    'holiday': 'alta',
    'ds': pd.to_datetime([
                            '2019-03-01', '2019-03-06', '2019-03-07', 
                            '2019-05-11', '2019-06-12', '2019-08-10',
                            '2019-11-29'
                            ]),
    'lower_window': 0,
    'upper_window': 0,
    })

    holidays = pd.concat((especial, alta))
    return holidays

import logging 
logging.getLogger('fbprophet').setLevel(logging.ERROR)

from itertools import product
from fbprophet import Prophet

from fbprophet.diagnostics import cross_validation
from fbprophet.diagnostics import performance_metrics

from tqdm import tqdm

param_grid = {  'growth': ["linear"], 
                'changepoints': [None], 
                'n_changepoints': [5], 
                'changepoint_range': [0.25, 0.5, 0.75],
                'yearly_seasonality': [False],
                'weekly_seasonality': [True],
                'daily_seasonality': [False],
                'holidays': [holidays],
                'seasonality_mode': ["additive"],
                'seasonality_prior_scale': [0.01, 0.1, 1.0, 10.0],
                'holidays_prior_scale': [10],
                'changepoint_prior_scale': [0.001, 0.01, 0.1, 0.5],
                'mcmc_samples': [0],
                'interval_width': [0.25, 0.5, 0.75],
                'uncertainty_samples': [0]
              }

args = list(product(*param_grid.values()))
len(args)

df_ps = pd.DataFrame()

for arg in tqdm(args):
    m = Prophet(*arg[:7], arg[7](), *arg[8:]).fit(df)
    cutoffs = pd.to_datetime(['2020-10-09', '2020-10-15', '2020-10-22'])
    df_cv = cross_validation(m, cutoffs=cutoffs, horizon='5 days')
    df_p = performance_metrics(df_cv, rolling_window=1)
    df_p['params'] = str(arg)
    df_ps = df_ps.append(df_p)

df_ps['mae+rmse'] = df_ps['mae']+df_ps['rmse']
df_ps = df_ps.sort_values(['mae+rmse'])
df_ps

df_ps.sort_values('rmse')