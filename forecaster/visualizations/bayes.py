import db
import pandas as pd
from yyyy_mm_dd import *

stds = {
    'Amsterdam': [0.19660064200323854, 0.2383552612223972, 0.24637917559070285, 0.2567377666273462, 0.2769345820649991, 0.25988795411934534, 0.2591418181970274, 0.2600691186768337, 0.26349445716168757, 0.2609331590767258, 0.26471109387051434, 0.2632894521789452, 0.2664901882334896, 0.2716871438013777, 0.2761305425003428, 0.2792497015187846, 0.2748464079452215, 0.2773755833560155, 0.2802023041210639, 0.28170403379954745, 0.28079213172340817, 0.28457807195483986, 0.29317417417635955, 0.29012371907354734, 0.2895611924361685, 0.2851722890963348, 0.2853692667424292, 0.28655691401895894, 0.29096525041866333, 0.29532291222576673, 0.30048861933874543, 0.29785852898074516, 0.2986015062933946, 0.2968000389931035, 0.29275546670577374, 0.2947239615901258, 0.30026705766973133, 0.3056589781873982, 0.3029437702556515, 0.30068563531702297, 0.3009011511906223, 0.30469307134998647, 0.299926244343794, 0.29192349828158914, 0.29297914307173195, 0.2904939589984911, 0.2969487842963446, 0.4392106721796901],
    'Rio de Janeiro': [0.047516448721903116, 0.0691692079040573, 0.08653805347981429, 0.10847364896060305, 0.12320037630092069, 0.1274704358828662, 0.154884148535676, 0.1575432022446098, 0.15660622988775713, 0.1576198151912777, 0.1619820032610724, 0.16214882522486612, 0.16269854063610603, 0.16338163383032514, 0.16444518146326423, 0.16140555232148884, 0.16063792418487738, 0.16324002796273862, 0.16658410506816432, 0.16517079998536555, 0.16711289602507337, 0.16922039084334678, 0.1704589338679017, 0.17085556126702076, 0.16730265168828884, 0.16703154084714095, 0.16625825868999594, 0.16406387528794086, 0.166249545521256, 0.16777455800749694, 0.17053978909383294, 0.1744050025960669, 0.1743879106817563, 0.171943079665187, 0.1713514730975283, 0.17491596393724035, 0.17836590797383942, 0.18104733199644482, 0.18153817528664623, 0.18345226629885036, 0.18376067244327532, 0.18298264240469791, 0.1861959978329796, 0.18776081810958783, 0.19343983206266643, 0.1964207284997987, 0.198598472912617, 0.4993764543424647],
}


def predictions_for(city):
    df = get_data(city)
    forecasts = {}
    for _, row in df.sort_values(by=['timestamp', 'forecast_delta'], ascending=False).iterrows():
        if len(forecasts.values()) >= 48:
            break
        if row.forecast_delta not in forecasts:
            forecasts[row.forecast_delta] = row
    forecasts = [adjust_forecast(city, df, row) for row in forecasts.values()]
    forecasts = sorted(forecasts, key=lambda x: x["forecast_for"])

    return forecasts


def adjust_forecast(city, df, row):
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

    probabilities = sorted(
        probabilities, key=lambda x: x["chance"], reverse=True)

    return {
        'forecast_for': row.forecast_for,
        'probabilities': probabilities,
        'precipitation': {
            'mu': row.precipitation / 100,
            'sigma': stds[city][row.forecast_delta]
        }
    }


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
