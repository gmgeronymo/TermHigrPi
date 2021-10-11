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

import time
import datetime
import configparser 	# ler arquivo de configuracao
from termhigr_functions import *       # funcoes auxiliares

# o arquivo config.ini reune as configuracoes que podem ser alteradas
config = configparser.ConfigParser()    # iniciar o objeto config
config.read('/boot/datalogger.ini')             # ler o arquivo de configuracao     

if (config['SensorConfig']['sensor'] == 'hygropalm') :
    import serial
    from hygropalm_serial import query_serial

elif (config['SensorConfig']['sensor'] == 'sato') :
    import serial
    from sato_serial import query_serial

else :
    import pigpio		# acesso a interface GPIO
    # configuracao do sensor
    # inicia interface pigpio
    pi = pigpio.pi()

    if not pi.connected:
        exit(0)
      
    if (config['SensorConfig']['sensor'] == 'DHT22') :
        import DHT22
        s = DHT22.sensor(pi, 22)

    if (config['SensorConfig']['sensor'] == 'BME280') :
        import BME280
        s = BME280.sensor(pi)

import csv          	# salvar dados antes de enviar ao DB
import sqlite3      	# banco de dados local
import os
#import os.path
from urllib.parse import urlencode
from urllib.request import Request, urlopen  # requests http

if __name__ == "__main__":
   
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
        REP_run = int(INTERVAL // INTERVAL_LCD)  # qtde rep ate salvar leitura
        REP_start = int(INTERVAL_START // INTERVAL_LCD) # valor inicial de REP para salvar em horarios 'redondos'
        #lcd = lcd_config()
        lcd = i2c_lcd.lcd(pi, width=16)
        counter = 0
        first_run = True
    else :
        # aguarda o proximo horario inteiro do intervalo para comecar     
        time.sleep((start-now).total_seconds()) # Overall INTERVAL second polling.

    next_reading = time.time()
   
    while True:
        data_atual = data_hora()

        # buscar leitura do sensor
        if (config['SensorConfig']['sensor'] == 'DHT22') :
            s.trigger()
            time.sleep(0.2)
            temperature = s.temperature()
            humidity = s.humidity()
            pressure = '';

        elif (config['SensorConfig']['sensor'] == 'BME280') :
            temperature, pressure, humidity = s.read_data()
        else :                  # sensors comerciais interface serial
            data_array = query_serial(config['SerialConfig'])
            temperature = float(data_array[1])
            humidity = float(data_array[0])

        
        # verificar se correcoes devem ser aplicadas
        if (config['CalConfig']['enable'] == 'true') :
            # carrega numpy para calcular correcoes
            from numpy import array, linalg, arange, ones, vstack
            # o arquivo cal.ini reune as informacoes da calibracao do termohigrometro
            cal = configparser.ConfigParser()
            cal.read('/boot/cal.ini')

            # calcular correcoes temperatura
            coeff_temp = corr_temp(cal)
            # calcular correcoes umidade
            coeff_umid = corr_umid(cal)

            # aplicar correcoes
            temperature = round((coeff_temp['a'] * temperature + coeff_temp['b']),1)
            humidity = round((coeff_umid['a'] * humidity + coeff_umid['b']),1)
        else :
            # valores sem correcao
            temperature = round(temperature,1)
            humidity = round(humidity,1)


        # LCD ativado
        if (config['LCDConfig']['enable'] == 'true') :
            lcd.put_line(0, data_atual['hora']+" "+"{0:.1f}".format(temperature)+chr(223)+"C")
            if (config['SensorConfig']['sensor'] == 'DHT22') :
                lcd.put_line(1, "{0:.1f}".format(humidity)+"% ")
            if (config['SensorConfig']['sensor'] == 'BME280') :
                lcd.put_line(1, "{0:.1f}".format(humidity)+"% "+"{0:.1f}".format(pressure/100)+" hPa")

            if (first_run) :
                REP = REP_start + 1
            else:
                REP = REP_run
            
            if (counter == REP) :
                log_txt(data_atual['ano'],data_atual['data'],data_atual['hora'],"{0:.1f}".format(humidity),"{0:.1f}".format(temperature),"{0:.1f}".format(pressure/100))
                salvar_sqlite(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100))
                if (config['HttpConfig']['enable'] == 'true') :
                    # se correcoes forem aplicadas, salvar dados do certificado de calibracao
                    if (config['CalConfig']['enable'] == 'true') :
                        salvar_http(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100), cal, url, api_key)
                    else :
                        salvar_http(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100), None, url, api_key)
                counter = 0
                first_run = False

            counter += 1 # incrementa contador   
            next_reading += INTERVAL_LCD
            time.sleep(next_reading-time.time())
            # sem LCD
        else :
            log_txt(data_atual['ano'],data_atual['data'],data_atual['hora'],"{0:.1f}".format(humidity),"{0:.1f}".format(temperature), "{0:.1f}".format(pressure/100))
            salvar_sqlite(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100))
            if (config['HttpConfig']['enable'] == 'true') :
                if (config['CalConfig']['enable'] == 'true') :
                    salvar_http(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100), cal, url, api_key)
                else :
                    salvar_http(data_atual['timestamp'],"{0:.1f}".format(temperature),"{0:.1f}".format(humidity), "{0:.1f}".format(pressure/100), None, url, api_key)
               
            next_reading += INTERVAL
            time.sleep(next_reading-time.time()) # Overall INTERVAL second polling.
	  
    if (lcd) :
        lcd.close()
	
    s.cancel()
    pi.stop()

