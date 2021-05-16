import error_reporting
import db
import csv
import io
import os
import numpy as np
from flask import Flask, make_response, render_template
from visualizations import bayes
from yyyy_mm_dd import *
app = Flask(__name__)


@app.route('/')
@app.route('/<city>')
def index(city="Amsterdam"):
    predictions = bayes.predictions_for(city)

    return render_template('bayes.html', today=today(), city=city, predictions=predictions, bell_curve_points=bell_curve_points)


def bell_curve_points(precipitation):
    mu = precipitation['mu']
    sigma = precipitation['sigma']

    bins = np.array(list(range(0, 101))) / 100
    line = np.exp(-(bins - mu)**2 / (2 * sigma**2))

    points = [("%.0f" % (x * 100)) + "," + ("%.2f" % (50 - (50 * y)))
              for x, y in zip(bins, line)]

    return " ".join(points)


@app.route('/csv')
def forecasts_csv():
    columns = ["timestamp", "type", "forecast_delta", "city", "summary",
               "precipitation", "temperature", "max", "min"]
    results = db.select("SELECT " + ", ".join(columns) + " FROM Forecasts")

    f = io.StringIO()
    writer = csv.writer(f, delimiter=',')
    writer.writerow(columns)
    rows = [[c.strip() if type(c) == str else c for c in list(r)]
            for r in results]
    writer.writerows(rows)

    output = make_response(f.getvalue())
    output.headers["Content-Disposition"] = "attachment; filename=forecasts.csv"
    output.headers["Content-type"] = "text/csv"
    return output


db.create_tables()
app.run(port=os.environ.get('PORT', 5000),
        debug=os.environ.get('APP_ENV', 'dev') == 'dev')
