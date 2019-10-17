#!/usr/bin/python3

# Termohigrometro utilizando RaspberryPi e um sensor DHT-22
# Autor: Gean Marcos Geronymo
# Data: 10/11/2016

# Modificado em 03/04/2019 - incluido suporte a interface REST
# envia os dados via requisicoes HTTP
# compativel com redes WiFi corporativas que bloqueam todas as portas TCP exceto 80 e 443
# Removido acesso direto ao DB externo

# Nova versao 16/10/2019
# Suporte a sensor BME280 via i2c
# Suporte a display LCD via i2c

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
      print("{}\t{}\t{}%\t{}ÂºC".format(data,hora,humidity,temperature), file=text_file)
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
   if not (os.path.isfile('logs/log.db')): # se o db nÃ£o existir, criar
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

def salvar_http(date, temperature, humidity, url, api_key):
   # escreve no buffer de saida
   write_buffer(temperature,humidity,date)
   try:
      d = open_buffer()
      for leitura in d:
         post_fields = {
           'temperature' : leitura['temperature'],
           'humidity' : leitura['humidity'],
           'date' : leitura['date']
         }
         request = Request(url, urlencode(post_fields).encode())
         request.add_header('X-API-KEY', api_key)
         # tenta enviar os dados via http 
         json = urlopen(request).read().decode()
         # apaga o buffer
         open('write_buffer.txt','w').close()
   except:
      dberror_log(data_atual['timestamp'])
      import subprocess
      subprocess.call("wpa_cli -i wlan0 reconfigure", shell=True)	     
   return

if __name__ == "__main__":

   # carrega as bibliotecas
   import time
   import pigpio		# acesso a interface GPIO
   import datetime     	# funcoes de data e hora
   import configparser 	# ler arquivo de configuracao
   import csv          	# salvar dados antes de enviar ao DB
   import sqlite3      	# banco de dados local
   import os.path
   from urllib.parse import urlencode
   from urllib.request import Request, urlopen  # requests http

   # inicia interface pigpio
   pi = pigpio.pi()

   if not pi.connected:
      exit(0)
   
   # o arquivo config.ini reune as configuracoes que podem ser alteradas

   config = configparser.ConfigParser()    # iniciar o objeto config
   # modificado em 03/04/2019 - arquivo de configuracao na particao /boot
   config.read('/boot/datalogger.ini')             # ler o arquivo de configuracao     

   # configuracao do sensor
   if (config['SensorConfig']['sensor'] == 'DHT22') :
      import DHT22
      s = DHT22.sensor(pi, 22)

   if (config['SensorConfig']['sensor'] == 'BME280') :
      import BME280
      s = BME280.sensor(pi)
   
   # configuracao para acessar o REST Server
   if (config['HttpConfig']['enable'] == 'true') :
      url = config['HttpConfig']['url']
      api_key = config['HttpConfig']['api_key']
      
   delta = datetime.timedelta(minutes=int(config['LogConfig']['interval']))
   INTERVAL = delta.total_seconds() # intervalo entre as leituras salvas (segundos)

   now = datetime.datetime.now()
   start = ceil_dt(now, delta) # inicia em horarios 'redondos'
   
 # verifica se opcao lcd esta habilitada
   if (config['LCDConfig']['enable'] == 'true') :
      import i2c_lcd
      refresh_lcd = datetime.timedelta(seconds=int(config['LCDConfig']['refresh']))
      INTERVAL_LCD = refresh_lcd.total_seconds()
      INTERVAL_START = (start-now).total_seconds()
      REP_run = int(INTERVAL // INTERVAL_LCD)  # qtde repetiÃ§Ãµes atÃ© salvar leitura
      REP_start = int(INTERVAL_START // INTERVAL_LCD) # valor inicial de REP para salvar em horarios 'redondos'
      #lcd = lcd_config()
      lcd = i2c_lcd.lcd(pi, width=16)
      counter = 0
      first_run = True
   else :
      # aguarda o proximo horario inteiro do intervalo para comeÃ§ar      
      time.sleep((start-now).total_seconds()) # Overall INTERVAL second polling.

   next_reading = time.time()
   
   while True:
      data_atual = data_hora()
      if (config['SensorConfig']['sensor'] == 'DHT22') :
         s.trigger()
         time.sleep(0.2)
         temperature = round(s.temperature(),1)      
         humidity = round(s.humidity())
         pressure = 'N/A';

      if (config['SensorConfig']['sensor'] == 'BME280') :
         t, p, h = s.read_data()
         temperature = round(t,2)      
         humidity = round(h,1)
         pressure = round(p,1)
      
      if (config['LCDConfig']['enable'] == 'true') :
         lcd.put_line(0, data_atual['hora'] + "    "+str(temperature)+" "+chr(223)+"C")
         lcd.put_line(1, str(humidity)+" %u.r. "+str(pressure)+ "hPa")
         

         if (first_run) :
            REP = REP_start + 1
         else:
            REP = REP_run
            
         if (counter == REP) :
            log_txt(data_atual['ano'],data_atual['data'],data_atual['hora'],humidity,temperature)
            salvar_sqlite(data_atual['timestamp'],str(temperature),str(humidity))
            if (config['HttpConfig']['enable'] == 'true') :
               salvar_http(data_atual['timestamp'],str(temperature),str(humidity), url, api_key)
            counter = 0
            first_run = False

         counter += 1 # incrementa contador   
         next_reading += INTERVAL_LCD
         time.sleep(next_reading-time.time())
      else :
         log_txt(data_atual['ano'],data_atual['data'],data_atual['hora'],humidity,temperature)
         salvar_sqlite(data_atual['timestamp'],str(temperature),str(humidity))
         if (config['HttpConfig']['enable'] == 'true') :
            salvar_http(data_atual['timestamp'],str(temperature),str(humidity), url, api_key)           
         next_reading += INTERVAL
         time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.
	  
   s.cancel()
   pi.stop()

