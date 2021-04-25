import psycopg2
import os


def connect():
    password = os.environ['POSTGRES_PASSWORD'] if 'POSTGRES_PASSWORD' in os.environ else 'password'
    conn = psycopg2.connect(database="forecaster", user="postgres",
                            password=password, host="127.0.0.1", port="5432")

    return conn


def create_tables():
    conn = connect()
    cur = conn.cursor()

    cur.execute('''
    CREATE TABLE IF NOT EXISTS Forecasts (
        id             SERIAL PRIMARY KEY     NOT NULL,
        city           CHAR(50)               NOT NULL,
        type           CHAR(50)               NOT NULL,
        datetime       TIMESTAMP              NOT NULL,
        summary        CHAR(50)               NOT NULL,
        precipitation  SMALLINT               NOT NULL,
        temperature    SMALLINT                       ,
        max            SMALLINT                       ,
        min            SMALLINT
    );
    CREATE INDEX IF NOT EXISTS forecasts_datetime_index ON Forecasts (datetime);
    ''')

    conn.commit()
    conn.close()
