import db
import pandas as pd
from yyyy_mm_dd import *


def predictions_for(city):
    df = get_data(city)
    forecasts = {}
    for _, row in df.sort_values(by=['timestamp', 'forecast_delta'], ascending=False).iterrows():
        if len(forecasts.values()) >= 48:
            break
        if row.forecast_delta not in forecasts:
            forecasts[row.forecast_delta] = row
    forecasts = [adjust_forecast(df, row) for row in forecasts.values()]
    forecasts = sorted(forecasts, key=lambda x: x["forecast_for"])

    return forecasts


def adjust_forecast(df, row):
    df = df[(df.forecast_delta == row.forecast_delta)]
    prediction = row.weather_type

    len_df = len(df)
    p_prediction = len(df[df.weather_type == prediction]) / len_df

    probabilities = {}
    for weather in df.weather_type.cat.categories:
        len_weather = len(df[df.weather_type_actual == weather])
        p_weather = len_weather / len_df
        if p_weather == 0:
            continue

        p_prediction_given_weather = len(df[(df.weather_type == prediction) & (
            df.weather_type_actual == weather)]) / len_weather
        # p_prediction_given_weather = (p_prediction * p_weather) / len_weather

        p_weather_given_prediction = 100 * (
            p_prediction_given_weather * p_weather) / p_prediction

        if p_weather_given_prediction > 1:
            probabilities[weather] = {
                'weather': weather, 'chance': round(p_weather_given_prediction)}

    probabilities = sorted(probabilities.values(),
                           key=lambda x: x["chance"], reverse=True)

    return {'forecast_for': row.forecast_for, 'probabilities': probabilities}


def get_data(city):
    columns = ["timestamp", "forecast_delta", "summary", "temperature"]
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
    df['timestamp'] = [start_of_yyyy_mm_dd_hh(
        timestamp) for timestamp in df['timestamp']]
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df['forecast_for'] = [move_yyyy_mm_dd_hh(timestamp, delta)
                          for timestamp, delta in zip(df['timestamp'], df['forecast_delta'])]
    # TODO: care about the wind
    df['weather_type'] = pd.Series([summary.replace(
        " / Wind", "") for summary in df['summary']]).astype("category")
    to_join = df[df.forecast_delta == 0].drop(columns=['forecast_for']).rename(
        columns={'timestamp': 'forecast_for'}).set_index(['forecast_for'])[['weather_type']].copy()
    df = df.join(
        to_join,
        on=['forecast_for'],
        how='left',
        rsuffix="_actual"
    )
    return df
