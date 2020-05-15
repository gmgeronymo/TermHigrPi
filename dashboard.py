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
    cur = conn.cursor()
    cur.execute("SELECT date, temperature, humidity, pressure FROM condicoes_ambientais")
    #r = [dict((cur.description[i][0], value) for i, value in enumerate(row)) for row in cur.fetchall()] 
    return cur.fetchall();
    
#    return (r[0] if r else None) if one else r

def select_last_24h_data(conn):
    cur = conn.cursor()
    # 27 hrs -> 24 hrs + 3 hrs (GMT-3)
    cur.execute("SELECT date, temperature, humidity, pressure FROM condicoes_ambientais WHERE date >= datetime('now', '-27 hours') AND date < datetime('now')")
    return cur.fetchall();

def select_last_month_data(conn):
    cur = conn.cursor()
    # 27 hrs -> 24 hrs + 3 hrs (GMT-3)
    cur.execute("SELECT date, temperature, humidity, pressure FROM condicoes_ambientais WHERE date >= datetime('now', '-1 month') AND date < datetime('now')")
    return cur.fetchall();

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
        pressure = my_query[0][3].replace('.',',');
        
    objDate = datetime.strptime(strDate, '%Y-%m-%d %H:%M:%S')
    meas_date = datetime.strftime(objDate,'%d/%m/%Y %H:%M:%S')
    
    return render_template('dashboard.html', date=meas_date, temp=temperature, hum=humidity, press=pressure)

@app.route('/grafico_24h')
def grafico_24h():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        my_query = select_last_24h_data(conn)
        ca_labels = [item[0] for item in my_query]
        ca_temp = [item[1] for item in my_query]
        ca_hum = [item[2] for item in my_query]
        ca_press = [item[3] for item in my_query]
    
    return render_template('multiple_chart.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press)

@app.route('/grafico_month')
def grafico_month():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        my_query = select_last_month_data(conn)
        ca_labels = [item[0] for item in my_query]
        ca_temp = [item[1] for item in my_query]
        ca_hum = [item[2] for item in my_query]
        ca_press = [item[3] for item in my_query]
    
    return render_template('multiple_chart.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press)

@app.route('/grafico_all')
def grafico_all():
    database = "logs/log.db"

    conn = create_connection(database)
    with conn:
        my_query = select_all_data(conn)
        ca_labels = [item[0] for item in my_query]
        ca_temp = [item[1] for item in my_query]
        ca_hum = [item[2] for item in my_query]
        ca_press = [item[3] for item in my_query]
    
    return render_template('multiple_chart.html', labels=ca_labels, temp=ca_temp, hum=ca_hum, press=ca_press)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
  