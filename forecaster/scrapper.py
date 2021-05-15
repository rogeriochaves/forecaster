import error_reporting
import parser
import db
import requests
import psycopg2
import psycopg2.extras
import os
import time
from prometheus_client import CollectorRegistry, Counter, push_to_gateway
from constants import CITY_CODES

APP_ENV = os.environ.get('APP_ENV', 'dev')

registry = CollectorRegistry()
counter = Counter('scrapped_forecasts',
                  'Amount of forecasts scrapped', registry=registry)


def run():
    db.create_tables()
    for city in CITY_CODES.keys():
        scrap_city_try_twice(city)

    if APP_ENV == 'prod':
        push_to_gateway('localhost:9091', job='scrapper.py', registry=registry)

    print("Done!")


def scrap_city_try_twice(name):
    try:
        scrap_city(name)
    except:
        print("Scrapping city " + name + " failed, trying again in 5s")
        time.sleep(5)
        scrap_city(name)


def scrap_city(name):
    code = CITY_CODES[name]

    req = requests.get('https://weather.com/en-GB/weather/tenday/l/' + code)
    forecasts = parser.extract_10_day_forecast(req.text)
    save(name, forecasts)
    counter.inc(len(forecasts))
    print("Saved 10 day forecast for", name)

    req = requests.get(
        'https://weather.com/en-GB/weather/hourbyhour/l/' + code)
    forecasts = parser.extract_hourly_forecast(req.text)
    save(name, forecasts)
    counter.inc(len(forecasts))
    print("Saved hourly forecast for", name)


def save(city, forecasts):
    values = []
    for forecast in forecasts:
        values.append((city, forecast['type'], forecast['forecast_delta'],
                      forecast['summary'], forecast['precipitation'],
                      forecast.get('temperature'), forecast.get('max'),
                      forecast.get('min')))

    conn = db.connect()
    cur = conn.cursor()

    psycopg2.extras.execute_values(cur,
                                   "INSERT INTO Forecasts (city, type, forecast_delta, summary, precipitation, temperature, max, min) VALUES %s",
                                   values
                                   )

    conn.commit()
    conn.close()


if __name__ == '__main__':
    run()
