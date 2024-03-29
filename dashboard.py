#!/usr/bin/python3

# Termohigrometro utilizando RaspberryPi e um sensor DHT-22
# Autor: Gean Marcos Geronymo
# Data: 15/05/2020

# dashboard usando flask e chartjs

from flask import Flask, Markup, render_template
import json
import sqlite3
from sqlite3 import Error
from datetime import datetime
import pandas as pd
import configparser

config = configparser.ConfigParser()
config.read('/boot/datalogger.ini')

# determina se existem dados sobre pressao atmosferica
if (config['SensorConfig']['sensor'] == 'BME280') :
    pressure_flag = True
else :
    pressure_flag = False


def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
    except Error as e:
        print(e)

    return conn

def select_last_row(conn):
    cur = conn.cursor()
    cur.execute("SELECT date, temperature, humidity, pressure FROM condicoes_ambientais ORDER BY id DESC LIMIT 1")
    return cur.fetchall();

def select_all_data(conn):
    query =  "SELECT date, temperature, humidity, pressure FROM condicoes_ambientais"
    df = pd.read_sql_query(query,conn,parse_dates={'date':'%Y-%m-%d %H:%M:%S'},index_col='date')
    df[['temperature','humidity','pressure']] = df[['temperature','humidity','pressure']].apply(pd.to_numeric)   
    #return df.resample('1D', how='mean')
    return df.resample('1D').agg(['mean','min','max'])

def select_last_24h_data(conn):
    query = "SELECT date, temperature, humidity, pressure FROM condicoes_ambientais WHERE date >= datetime('now', '-27 hours') AND date < datetime('now')"
    return pd.read_sql_query(query,conn,parse_dates={'date':'%Y-%m-%d %H:%M:%S'},index_col='date')

def select_last_month_data(conn):
    query = "SELECT date, temperature, humidity, pressure FROM condicoes_ambientais WHERE date >= datetime('now', '-1 month') AND date < datetime('now')" 
    df = pd.read_sql_query(query,conn,parse_dates={'date':'%Y-%m-%d %H:%M:%S'},index_col='date')
    df[['temperature','humidity','pressure']] = df[['temperature','humidity','pressure']].apply(pd.to_numeric)   
    #return df.resample('120Min', how='mean')
    return df.resample('1D').agg(['mean','min','max'])

app = Flask(__name__)

@app.route('/')
def index():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        my_query = select_last_row(conn)
        strDate = my_query[0][0];
        temperature = my_query[0][1].replace('.',',');
        humidity = my_query[0][2].replace('.',',');
        if (my_query[0][3]) :
            pressure = my_query[0][3].replace('.',',')
        else :
            pressure = None
        
    objDate = datetime.strptime(strDate, '%Y-%m-%d %H:%M:%S')
    meas_date = datetime.strftime(objDate,'%d/%m/%Y %H:%M:%S')
    
    return render_template('dashboard.html', date=meas_date, temp=temperature, hum=humidity, press=pressure, flag=pressure_flag)

@app.route('/grafico_24h')
def grafico_24h():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        df = select_last_24h_data(conn)
        ca_labels = df.index.strftime('%d/%m/%Y %H:%M:%S').tolist()
        ca_temp = df['temperature'].tolist()
        ca_hum = df['humidity'].tolist()
        ca_press = df['pressure'].tolist()
    return render_template('multiple_chart.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press, flag=pressure_flag)

@app.route('/grafico_month')
def grafico_month():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        df = select_last_month_data(conn)
        ca_labels = df.index.strftime('%d/%m/%Y %H:%M:%S').tolist()
        
        ca_temp = df['temperature']['mean'].tolist()
        ca_hum = df['humidity']['mean'].tolist()
        ca_press = df['pressure']['mean'].tolist()

        ca_temp_min = df['temperature']['min'].tolist()
        ca_hum_min = df['humidity']['min'].tolist()
        ca_press_min = df['pressure']['min'].tolist()

        ca_temp_max = df['temperature']['max'].tolist()
        ca_hum_max = df['humidity']['max'].tolist()
        ca_press_max = df['pressure']['max'].tolist()
        
    return render_template('multiple_chart_maxmin.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press, temp_min=ca_temp_min, hum_min=ca_hum_min, press_min=ca_press_min, temp_max=ca_temp_max, hum_max=ca_hum_max, press_max=ca_press_max, flag=pressure_flag)

@app.route('/grafico_all')
def grafico_all():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        df = select_all_data(conn)
        ca_labels = df.index.strftime('%d/%m/%Y %H:%M:%S').tolist()

        ca_temp = df['temperature']['mean'].tolist()
        ca_hum = df['humidity']['mean'].tolist()
        ca_press = df['pressure']['mean'].tolist()

        ca_temp_min = df['temperature']['min'].tolist()
        ca_hum_min = df['humidity']['min'].tolist()
        ca_press_min = df['pressure']['min'].tolist()

        ca_temp_max = df['temperature']['max'].tolist()
        ca_hum_max = df['humidity']['max'].tolist()
        ca_press_max = df['pressure']['max'].tolist()
    
    return render_template('multiple_chart_maxmin.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press, temp_min=ca_temp_min, hum_min=ca_hum_min, press_min=ca_press_min, temp_max=ca_temp_max, hum_max=ca_hum_max, press_max=ca_press_max, flag=pressure_flag)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
  
