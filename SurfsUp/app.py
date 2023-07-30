# Import the dependencies.
import numpy as np
import datetime as dt
import pandas as pd
from flask import Flask, jsonify
from sqlalchemy import create_engine, func
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session

#################################################
# Database Setup
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)


# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.measurement
# Create our session (link) from Python to the DB
session = Session(bind=engine)
#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"/api/v1.0/stations<br/>"
        f"/api/v1.0/tobs<br/>"
        f"/api/v1.0/&lt;start&gt;<br/>"
        f"/api/v1.0/&lt;start&gt;/&lt;end&gt;<br/>"
    )

@app.route("/api/v1.0/precipitation")
def precipitation():
    """Convert the query results to a dictionary using date as the key and prcp as the value."""
    session = Session(bind=engine)
    results = session.query(measurement.date, measurement.prcp).\
              filter(measurement.date >= dt.date(2016, 8, 23)).all()
    session.close()
    precipitation_data = {date: prcp for date, prcp in results}
    return jsonify(precipitation_data)
    
@app.route("/api/v1.0/stations")
def stations():
    """Return a JSON list of stations from the dataset."""
    session = Session(bind=engine)
    results = session.query(measurement.station).group_by(measurement.station).all()

    all_stations = list(np.ravel(results))
    return jsonify(all_stations)
    session.close()

@app.route("/api/v1.0/tobs")
def tobs():
    """Query the dates and temperature observations of the most-active station for the previous year of data."""
    session = Session(bind=engine)
    results_date = session.query(func.max(measurement.date)).scalar()
    latest_date = dt.datetime.strptime(results_date, "%Y-%m-%d")
    one_year_ago = latest_date - dt.timedelta(days=365)

    results = session.query(measurement.date, measurement.tobs).\
              filter(measurement.station == "USC00519281").\
              filter(measurement.date >= one_year_ago).all()

    
    temperature_data = []
    for date, tobs in results:
        temp_dict = {}
        temp_dict["date"] = date
        temp_dict["tobs"] = tobs
        temperature_data.append(temp_dict)

    return jsonify(temperature_data)
    session.close()


@app.route("/api/v1.0/<start>")
@app.route("/api/v1.0/<start>/<end>")
def temperature_stats(start=None, end=None):
    """Return a JSON list of the minimum, average, and maximum temperatures for a given start or start-end range."""
    session = Session(engine)
    def calc_temps(start_date, end_date):
        return session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
               filter(measurement.date >= start_date).filter(measurement.date <= end_date).all()

    # If end date is not provided, use the latest date in the dataset
    if not end:
        end = session.query(func.max(measurement.date)).scalar()

    # Calculate the temperature statistics
    temperature_stats = calc_temps(start, end)

    # Create a dictionary with the temperature statistics
    temp_stats_dict = {
        "start_date": start,
        "end_date": end,
        "TMIN": temperature_stats[0][0],
        "TAVG": temperature_stats[0][1],
        "TMAX": temperature_stats[0][2]
    }

    return jsonify(temp_stats_dict)

if __name__ == "__main__":
    app.run(debug=True)
