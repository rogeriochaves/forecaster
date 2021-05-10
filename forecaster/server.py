import error_reporting
import db
import csv
import io
import os
from flask import Flask, make_response, render_template
from visualizations import bayes
from yyyy_mm_dd import *
app = Flask(__name__)


@app.route('/')
@app.route('/<city>')
def index(city="Amsterdam"):
    predictions = bayes.predictions_for(city)

    return render_template('bayes.html', today=today(), city=city, predictions=predictions)


@app.route('/csv')
def forecasts_csv():
    conn = db.connect()
    cur = conn.cursor()
    columns = ["timestamp", "type", "forecast_delta", "city", "summary",
               "precipitation", "temperature", "max", "min"]
    cur.execute("SELECT " + ", ".join(columns) + " FROM Forecasts;")
    results = cur.fetchall()
    conn.close()

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
