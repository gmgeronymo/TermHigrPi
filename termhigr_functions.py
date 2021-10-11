#!/usr/bin/python3
# funcoes comuns aos programas do termo higrometro
def ceil_dt(dt, delta):
    return dt + (datetime.datetime.min - dt) % delta

def data_hora():
    date = datetime.datetime.now();
    timestamp = datetime.datetime.strftime(date, '%Y-%m-%d %H:%M:%S')
    data = datetime.datetime.strftime(date, '%d/%m/%Y')
    hora = datetime.datetime.strftime(date, '%H:%M:%S')
    ano = datetime.datetime.strftime(date, '%Y')
    return {'timestamp':timestamp, 'data':data, 'hora':hora, 'ano':ano}

def corr_temp(cal):
    # calcula correcoes para temperatura
    x_temperature = cal['Temperatura']['indicacoes'].split(',')
    x_temperature = array([float(a) for a in x_temperature])
    temperature_correcoes = cal['Temperatura']['correcoes'].split(',')
    temperature_correcoes = array([float(a) for a in temperature_correcoes])
    y_temperature = x_temperature + temperature_correcoes
    # minimos quadrados
    A = vstack([x_temperature, ones(len(x_temperature))]).T
    a, b = linalg.lstsq(A, y_temperature)[0]
    # temperature = a1*x + b1
    return {'a':a, 'b':b}

def corr_umid(cal):
    # calcula correcoes para a umidade
    x_humidity = cal['Umidade']['indicacoes'].split(',')
    x_humidity = array([float(a) for a in x_humidity])
    humidity_correcoes = cal['Umidade']['correcoes'].split(',')
    humidity_correcoes = array([float(a) for a in humidity_correcoes])
    y_humidity = x_humidity + humidity_correcoes
    # minimos quadrados
    A = vstack([x_humidity, ones(len(x_humidity))]).T
    a, b = linalg.lstsq(A, y_humidity)[0]
    # humidity = a2*x + b2
    return {'a':a, 'b':b}

# parametro pressure eh opcional
def log_txt(ano,data,hora,humidity,temperature,pressure=None):
    with open("logs/log_"+ano+".txt","a",encoding="iso-8859-1",newline="\r\n") as text_file:
        if (pressure) :
            print("{}\t{}\t{}%\t{} ºC\t{} hPa".format(data,hora,humidity,temperature,pressure), file=text_file)
        else :
            print("{}\t{}\t{}%\t{} ºC".format(data,hora,humidity,temperature), file=text_file)
        text_file.close();
    return

def dberror_log(timestamp):
    import traceback
    with open("logs/dberror.log","a") as text_file:
        print("{}   Erro ao conectar com o banco de dados \n".format(timestamp), file=text_file)
        traceback.print_exc(file=text_file)
        text_file.close();
    return

def write_buffer(timestamp,temperature,humidity,pressure,certificado,data_certificado):
    with open("write_buffer.txt","a") as csvfile:
        write_buffer = csv.writer(csvfile, delimiter=',',lineterminator='\n')
        write_buffer.writerow([timestamp,str(temperature),str(humidity),str(pressure),certificado,data_certificado])
        csvfile.close();
    return

def open_buffer():
    with open("write_buffer.txt") as csvfile:
        reader = csv.DictReader(csvfile,delimiter=',',fieldnames=['date','temperature','humidity','pressure','certificado','data_certificado'])
        d = list(reader)
        csvfile.close();
    return d

def salvar_sqlite(date,temperature,humidity,pressure=None):
    if not (pressure) :
        pressure = ''
    
    if not (os.path.isfile('logs/log.db')): # se o db nao existir, criar
        conn = sqlite3.connect('logs/log.db')
        c = conn.cursor()
        c.execute("""DROP TABLE IF EXISTS condicoes_ambientais""")
        c.execute("""CREATE TABLE condicoes_ambientais (
        id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	date TEXT,
	temperature TEXT,
	humidity TEXT,
	pressure TEXT
        );
        """)
        conn.close()
        conn = sqlite3.connect('logs/log.db')
        cur = conn.cursor()
        cur.execute("""INSERT INTO condicoes_ambientais (date, temperature, humidity, pressure) VALUES (?, ?, ?, ?)""", (date, temperature, humidity, pressure))
        conn.commit()
        conn.close()

    return

def salvar_http(date, temperature, humidity, pressure, cal, url, api_key):

    if (cal) :
        # dados do certificado de calibracao do termohigrometro
        certificado = cal['Certificado']['certificado']
        data_certificado = cal['Certificado']['data']
    else :
        certificado = ''
        data_certificado = ''

    if not (humidity) :
        humidity = ''
        
    # escreve no buffer de saida
    write_buffer(date,temperature,humidity,pressure,certificado,data_certificado)
   
    try:
        d = open_buffer()
        for leitura in d:
            post_fields = {
                'temperature' : leitura['temperature'],
                'humidity' : leitura['humidity'],
                'pressure' : leitura['pressure'],
                'date' : leitura['date'],
                'certificado': leitura['certificado'],
                'data_certificado': leitura['data_certificado']
            }
            request = Request(url, urlencode(post_fields).encode())
            request.add_header('X-API-KEY', api_key)
            # tenta enviar os dados via http 
            json = urlopen(request).read().decode()
            # apaga o buffer
            open('write_buffer.txt','w').close()
    except:
        dberror_log(date)
    return

