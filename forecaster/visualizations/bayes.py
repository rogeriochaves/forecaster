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

    sigmas = get_sigmas(city)
    adjusted_forecasts = []
    for row in forecasts.values():
        adjusted = {'forecast_for': row.forecast_for}
        adjusted['temperature'] = row.temperature
        adjusted['probabilities'] = weather_probabilities(df, row)
        adjusted['precipitation'] = precipitation_bell_curve(sigmas, row)
        adjusted_forecasts.append(adjusted)

    adjusted_forecasts.reverse()
    return adjusted_forecasts


def weather_probabilities(df, row):
    df = df[(df.forecast_delta == row.forecast_delta)]
    prediction = row.weather_type

    len_df = len(df)
    p_prediction = len(df[df.weather_type == prediction]) / len_df

    probabilities = {}
    for weather in df.weather_type.cat.categories:
        df_weather = df[df.weather_type_actual == weather]
        p_weather = len(df_weather) / len_df
        if p_weather == 0:
            continue

        p_prediction_given_weather = len(
            df_weather[df_weather.weather_type == prediction]) / len(df_weather)

        p_weather_given_prediction = (
            p_prediction_given_weather * p_weather) / p_prediction

        group = weather_group(weather)
        probabilities[group] = \
            probabilities.get(group, 0) + p_weather_given_prediction

    probabilities = [{
        'weather': key,
        'chance': round(100 * chance)
    } for key, chance in probabilities.items() if chance > 0.01]

    return sorted(probabilities, key=lambda x: x["chance"], reverse=True)


def precipitation_bell_curve(sigmas, row):
    return {
        'mu': row.precipitation / 100,
        'sigma': 0 if row.forecast_delta == 0 else sigmas[row.forecast_delta - 1]
    }


def get_sigmas(city):
    sigmas = db.select(
        "SELECT data FROM PrecipitationSigmas where city = %s", (city,))
    sigmas = sigmas[0][0]['hourly']

    return sigmas


def weather_group(weather):
    if 'Sunny' in weather:
        return 'Sunny'
    elif 'Clear' in weather:
        return 'Clear'
    elif 'Cloudy' in weather:
        return 'Cloudy'
    elif 'T-' in weather:
        return 'T-Storms'
    elif 'Showers' in weather:
        return 'Showers'
    elif 'Rain' in weather:
        return 'Rain'
    return weather


def get_data(city):
    columns = ["timestamp", "forecast_delta",
               "summary", "temperature", "precipitation"]
    result = db.select("SELECT " + ", ".join(columns) +
                       " FROM Forecasts WHERE type='hourly' AND city = %s", (city,))

    return build_df(result, columns)


def build_df(data, columns):
    df = pd.DataFrame(data, columns=columns)
    df['timestamp'] = [start_of_yyyy_mm_dd_hh(
        timestamp) for timestamp in df['timestamp']]
    df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
    df['forecast_for'] = [move_yyyy_mm_dd_hh(timestamp, delta)
                          for timestamp, delta in zip(df['timestamp'], df['forecast_delta'])]
    # TODO: care about the wind
    df['weather_type'] = pd.Series([summary.replace(
        " / Wind", "").strip() for summary in df['summary']]).astype("category")
    to_join = df[df.forecast_delta == 0].drop(columns=['forecast_for']).rename(
        columns={'timestamp': 'forecast_for'}).set_index(['forecast_for'])[['weather_type']].copy()
    df = df.join(
        to_join,
        on=['forecast_for'],
        how='left',
        rsuffix="_actual"
    )
    return df
