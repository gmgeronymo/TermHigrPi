#!/usr/bin/python3

def query_serial(serialconfig):
    # configuracao da conexao serial
    # seguindo informacoes do manual do fabricante
    ser = serial.Serial(
        port=serialconfig['port'],
        baudrate=19200,
        parity=serial.PARITY_EVEN,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.SEVENBITS,
        timeout = int(serialconfig['timeout'])
    )

    querystring = serialconfig['querystring']
    # envia para o termohigrometro a query string com o terminador de linha \r
    #ser.write(b'{u00RDD}\r')
    ser.write((querystring+'\r').encode())

    # le a resposta do termohigrometro
    rcv_str = ser.read(50)
    # fecha a conexao serial
    ser.close()

    # transformar o byte object recebido em uma string
    dec_str = rcv_str.decode('utf-8')
    # processa a string para extrair os valores de temperatura e umidade
    # o termohigrometro retorna uma string do tipo:
    # '{u00RDD 0071.68;0022.78;----.--;----.--;#6\r'
    # o comando abaixo remove o trecho
    # '{u00RDD '
    # Assim, e possivel separar temperatura e umidade utilizando ';'
    data_array = (dec_str.replace(querystring.replace('}',' '),'')).split(';')
    # arredonda a temperatura e umidade para uma casa decimal
    return data_array


