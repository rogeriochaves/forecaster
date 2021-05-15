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
        timestamp      TIMESTAMP              NOT NULL DEFAULT NOW(),
        forecast_delta SMALLINT               NOT NULL,
        city           CHAR(50)               NOT NULL,
        type           CHAR(50)               NOT NULL,
        summary        CHAR(50)               NOT NULL,
        precipitation  SMALLINT               NOT NULL,
        temperature    SMALLINT                       ,
        max            SMALLINT                       ,
        min            SMALLINT
    );
    CREATE INDEX IF NOT EXISTS forecasts_index ON Forecasts (type, timestamp, forecast_delta);

    CREATE TABLE IF NOT EXISTS PrecipitationSigmas (
        city           CHAR(50) PRIMARY KEY   NOT NULL,
        data           JSONB                  NOT NULL,
        updated_at     TIMESTAMP              NOT NULL
    );
    ''')

    conn.commit()
    conn.close()


def insert(query, args):
    conn = connect()
    cur = conn.cursor()

    cur.execute(query, args)

    conn.commit()
    conn.close()
