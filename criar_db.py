#!/usr/bin/python3

import sqlite3

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
print ("Tabela criada com sucesso.")
conn.close()

