#!/usr/bin/python3

# Termohigrometro utilizando RaspberryPi e um sensor DHT-22
# Autor: Gean Marcos Geronymo
# Data: 10/11/2016

def ceil_dt(dt, delta):
   return dt + (datetime.datetime.min - dt) % delta

def data_hora():
   date = datetime.datetime.now();
   timestamp = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
   data = datetime.datetime.strftime(date, '%d/%m/%Y')
   hora = datetime.datetime.strftime(date, '%H:%M:%S')
   ano = datetime.datetime.strftime(date, '%Y')
   return {'timestamp':timestamp, 'data':data, 'hora':hora, 'ano':ano}

def log_txt(ano,data,hora,humidity,temperature):
   with open("logs/log_"+ano+".txt","a",encoding="iso-8859-1",newline="\r\n") as text_file:
      print("{}\t{}\t{}%\t{}ºC".format(data,hora,humidity,temperature), file=text_file)
      text_file.close();
   return

def dberror_log(timestamp):
   import traceback
   with open("logs/dberror.log","a") as text_file:
      print("{}   Erro ao conectar com o banco de dados \n".format(timestamp), file=text_file)
      traceback.print_exc(file=text_file)
      text_file.close();
   return

def write_buffer(temperature,humidity,timestamp):
   with open("write_buffer.txt","a") as csvfile:
      write_buffer = csv.writer(csvfile, delimiter=',',lineterminator='\n')
      #      write_buffer.writerow([str(temperature),str(humidity),timestamp,cal['Certificado']['certificado'],cal['Certificado']['data']])
      write_buffer.writerow([str(temperature),str(humidity),timestamp])
      csvfile.close();
   return

def open_buffer():
   with open("write_buffer.txt") as csvfile:
      reader = csv.DictReader(csvfile,delimiter=',',fieldnames=['temperature','humidity','date','certificado','data_certificado'])
      d = list(reader)
      csvfile.close();
   return d

def salvar_sqlite(date,temperature,humidity):
   if not (os.path.isfile('logs/log.db')): # se o db não existir, criar
      conn = sqlite3.connect('logs/log.db')
      c = conn.cursor()
      c.execute("""DROP TABLE IF EXISTS condicoes_ambientais""")
      c.execute("""CREATE TABLE condicoes_ambientais (
			id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
			date TEXT,
			temperature TEXT,
			humidity TEXT
      );
      """)
      conn.close()
   conn = sqlite3.connect('logs/log.db')
   cur = conn.cursor()
   cur.execute("""INSERT INTO condicoes_ambientais (date, temperature, humidity) VALUES (?, ?, ?)""", (date, temperature, humidity))
   conn.commit()
   conn.close()

   return

if __name__ == "__main__":

   # carrega as bibliotecas
   import time
   import pigpio
   import DHT22
   import psycopg2     # interface com PostgreSQL
   import datetime     # funcoes de data e hora
   import configparser # ler arquivo de configuracao
   import csv          # salvar dados antes de enviar ao DB
   import sqlite3      # banco de dados local
   import os.path
   import Adafruit_CharLCD as LCD # escrever no LCD
 
   # o arquivo config.ini reune as configuracoes que podem ser alteradas

   config = configparser.ConfigParser()    # iniciar o objeto config
   config.read('config/config.ini')             # ler o arquivo de configuracao

   delta = datetime.timedelta(minutes=int(config['DHTConfig']['interval']))
   INTERVAL = delta.total_seconds() # intervalo entre as leituras (segundos)
   pi = pigpio.pi()
   s = DHT22.sensor(pi, 22)

   # configuracao do display LCD
   # Raspberry Pi pin configuration:
   lcd_rs        = 25
   lcd_en        = 24
   lcd_d4        = 23
   lcd_d5        = 17
   lcd_d6        = 18
   lcd_d7        = 21
   lcd_backlight = 4

   # Define LCD column and row size for 16x2 LCD.
   lcd_columns = 16
   lcd_rows    = 2

   # Initialize the LCD using the pins above.
   lcd = LCD.Adafruit_CharLCD(lcd_rs, lcd_en, lcd_d4, lcd_d5, lcd_d6, lcd_d7, lcd_columns, lcd_rows, lcd_backlight)

   # primeira execucao
   data_atual = data_hora()
   s.trigger()
   time.sleep(0.2)
   temperature = round(s.temperature(),1)
   humidity = round(s.humidity())

   lcd.clear()
   lcd.message(data_atual['data']+' '+data_atual['hora']+'\n'+str(temperature)+' '+chr(223)+'C '+str(humidity)+' %u.r.')


   # aguarda o proximo horario inteiro do intervalo para começar
   now = datetime.datetime.now()
   start = ceil_dt(now, delta)
   time.sleep((start-now).total_seconds()) # Overall INTERVAL second polling.
   
   next_reading = time.time()
   while True:
      data_atual = data_hora()
      s.trigger()
      time.sleep(0.2)
      temperature = round(s.temperature(),1)
      humidity = round(s.humidity())

      lcd.clear()
      lcd.message(data_atual['data']+' '+data_atual['hora']+'\n'+str(temperature)+' '+chr(223)+'C '+str(humidity)+' %u.r.')

      log_txt(data_atual['ano'],data_atual['data'],data_atual['hora'],humidity,temperature)
      salvar_sqlite(data_atual['timestamp'],str(temperature),str(humidity))

      if config['DatabaseConfig'].getboolean('external_db'):
         write_buffer(temperature,humidity,data_atual['timestamp'])
         try:
            conn = psycopg2.connect("dbname={} user={} password={} host={}".format(config['DatabaseConfig']['dbname'],config['DatabaseConfig']['user'],config['DatabaseConfig']['password'],config['DatabaseConfig']['host']))
            d = open_buffer()
            cur = conn.cursor()
            cur.executemany("""INSERT INTO raspberry (temperature, humidity, date) VALUES (%(temperature)s, %(humidity)s, %(date)s);""",d)
            open('write_buffer.txt','w').close()
            # salva as alteracoes
            conn.commit()
            cur.close()
            # fecha a conexao
            conn.close()
         except:
            dberror_log(data_atual['timestamp'])
            
      next_reading += INTERVAL
      time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.

   s.cancel()
   pi.stop()

