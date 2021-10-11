#!/usr/bin/python3

import serial

def query_serial(serialconfig):
    # configuracao da conexao serial
    # adaptado para termohigrometro SATO
    ser = serial.Serial(
        port=serialconfig['port'],
        baudrate=19200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.SEVENBITS,
        timeout = int(serialconfig['timeout'])
    )

    # le uma linha do termohigrometro
    rcv_str = ser.readline()
    # fecha a conexao serial
    ser.close()

    # transformar o byte object recebido em uma string
    dec_str = rcv_str.decode('utf-8')
    # processa a string para extrair os valores de temperatura e umidade
    data = dec_str.split()
    temperature = float(data[1].replace(',',''))/10
    humidity = float(data[2])/10
    
    data_array = [str(humidity), str(temperature)]
    return data_array


