import os
import db
import pymc3 as pm
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import json
from prometheus_client import CollectorRegistry, Counter, Gauge, push_to_gateway
from constants import CITIES
from yyyy_mm_dd import *

APP_ENV = os.environ.get('APP_ENV', 'dev')

registry = CollectorRegistry()
counter = Counter('batch_process_adjustments',
                  'Cities processed for their adjustments', ['city'], registry=registry)

accuracy_gauge = Gauge('precipitation_plus_sigma_accuracy',
                       'Accuracy of weather predictions +- sigma', ['city'], registry=registry)
range_sizes_gauge = Gauge('precipitation_range_sizes',
                          'Range sizes used in accuracy calculation, basically sigma capped at 0 and 100', ['city'], registry=registry)


def run():
    print("Starting...")
    db.create_tables()
    for city in CITIES:
        hourly_sigmas = calculate_sigmas(city)
        save_sigmas(city, {'hourly': hourly_sigmas})
        print("Saved sigmas for", city)

        counter.labels(city).inc()

        if APP_ENV == 'prod':
            push_to_gateway('localhost:9091',
                            job='scrapper.py', registry=registry)

    print("Done!")


def calculate_sigmas(city):
    df = get_hourly_data(city)

    print("Building sigmas model for", city)
    basic_model = pm.Model()

    df = df[(df.forecast_delta > 0)]
    deltas = df['forecast_delta']
    X = df['precipitation']
    y = df['precipitation_actual']

    with basic_model:
        sigmas = pm.Uniform('sigmas', lower=0, upper=1, shape=len(set(deltas)))
        actual = pm.Normal("actual", mu=X, sd=sigmas[deltas - 1], observed=y)
        trace = pm.sample(500)

    collect_stats(df, city, trace)

    return [trace['sigmas'].T[delta - 1].mean() for delta in sorted(set(deltas))]


def collect_stats(df, city, trace):
    inside_range = 0
    range_sizes = []
    for _, row in df.iterrows():
        delta = row['forecast_delta']
        X = row['precipitation']
        y = row['precipitation_actual']

        sigma = np.mean(trace['sigmas'].T[delta - 1])

        min_ = max(X - sigma, 0)
        max_ = min(X + sigma, 1)
        range_sizes.append(max_ - min_)
        if y >= min_ and y <= max_:
            inside_range += 1

    accuracy = inside_range / len(df)
    accuracy_gauge.labels(city).set(accuracy)
    print("accuracy", accuracy, "%")

    range_sizes_gauge.labels(city).set(np.mean(range_sizes))
    print("range_sizes", np.mean(range_sizes))


def save_sigmas(city, data):
    db.insert("INSERT INTO PrecipitationSigmas(city, data, updated_at) VALUES (%s, %s, NOW())",
              (city, json.dumps(data)))


def get_hourly_data(city):
    print("Getting hourly data for", city)
    columns = ["timestamp", "forecast_delta",
               "summary", "temperature", "precipitation"]
    conn = db.connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT " +
        ", ".join(
            columns) + " FROM Forecasts WHERE type='hourly' AND city=%s;",
        (city,)
    )
    result = cur.fetchall()
    conn.close()

    return build_df(result, columns)


def build_df(data, columns):
    df = pd.DataFrame(data, columns=columns)
    df['precipitation'] /= 100
    df['timestamp'] = [start_of_yyyy_mm_dd_hh(
        timestamp) for timestamp in df['timestamp']]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['forecast_for'] = [move_yyyy_mm_dd_hh(timestamp, delta)
                          for timestamp, delta in zip(df['timestamp'], df['forecast_delta'])]
    # TODO: care about the wind
    df['weather_type'] = pd.Series([summary.replace(
        " / Wind", "").strip() for summary in df['summary']]).astype("category")
    to_join = df[df.forecast_delta == 0].drop(columns=['forecast_for']).rename(
        columns={'timestamp': 'forecast_for'})[['forecast_for', 'weather_type', 'precipitation']].copy().reset_index()
    to_join = to_join.set_index(['forecast_for'])

    df = df.join(
        to_join,
        on=['forecast_for'],
        how='inner',
        rsuffix="_actual"
    )
    return df


if __name__ == '__main__':
    run()
