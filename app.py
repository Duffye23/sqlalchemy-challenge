# Import the dependencies.
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import datetime as dt
import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func
from sqlalchemy import inspect, distinct
from flask import Flask, jsonify

#################################################
# Database Setup
#################################################

# Create an engine for the chinook.sqlite database
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
# reflect an existing database into a new model
Base = automap_base()

# reflect the tables
#Base.reflect(autoload_with=engine)
Base.prepare(engine, reflect=True)
#Check our tables if need be
Base.classes.keys()
# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station
# Create our session (link) from Python to the DB
session = Session(bind=engine)

#################################################
# Flask Setup
#################################################
app = Flask(__name__)


#################################################
# Flask Routes
#################################################
#Create each route and code in what they do
#Homepage
@app.route("/")
def welcome():
    """List all available api routes."""
    return (
        f"Available Routes:<br/>"
        f"<'/api/v1.0/prcp'>/api/v1.0/prcp<br/>"
        f"<'/api/v1.0/station'>/api/v1.0/station<br/>"
        f"<'/api/v1.0/tobs'>/api/v1.0/tobs<br/>"
        f"<'/api/v1.0/<start'>/api/v1.0/<start><br/>"
        f"<'/api/v1.0/<start>/<end'>/api/v1.0/<start>/<end><br/>"
    )


#Precipitation queries
@app.route("/api/v1.0/prcp")
def prcp():
    """Return a list of precipitation and date data from the database"""
    #We know the last date in the data is 2016-08-23 from the previous section
    last_year_prcp = session.query(measurement.date, measurement.prcp).filter(measurement.date > '2016-08-22').order_by(measurement.date).all()
    session.close()

    #Take the prcp queries and put into a dictionary to be transformed into a json file
    prcp_values = []
    for prcp, date in last_year_prcp:
        prcp_dict = {}
        prcp_dict['Precipitqation'] = prcp
        prcp_dict['Date'] = date
        last_year_prcp.append(prcp_dict)
    return jsonify(prcp_values)


#Station queries: Return a JSON list of stations from the dataset
@app.route("/api/v1.0/station")
def station(): 
    """Return a list of stations from the database""" 
    station_qry = session.query(station.station, station.id).all()
    
#Take the station queries and put into a dictionary to be transformed into a json file
    stations_list = []
    for station, id in station_qry:
        stations_dict = {}
        stations_dict['station'] = station
        stations_dict['id'] = id
        stations_list.append(stations_dict)
    return jsonify (stations_list) 


#Tobs queries: Return a JSON list of temperatures from the last year from the most active station.
@app.route("/api/v1.0/tobs")
def tobs():
    """Return a JSON list of temperature observations for the previous year from the most active station."""
    #order by descending (or ascending) for the easiest way to find the last entered date and the end point of the query.
    past_year_obs = session.query(measurement.date, measurement).order_by(measurement.date.desc()).first()
    print(past_year_obs)
    #transorm the query into datetime so it can be used
    past_year_start = dt.date(2016,8,23)

    #find the most active station
    active_station_list = session.query(measurement.station, func.count(measurement.station)).order_by(func.count(measurement.station).desc()).\
        group_by(measurement.station).first()
    most_active_station = active_station_list[0]

    #use the the past year for our range and the most active station query
    past_year_tobs_qry = session.query(measurement.date, measurement.tobs, measurement.station).filter(measurement.date > past_year_start).\
        filter(measurement.station == most_active_station) 
    
    session.close()

    tobs_list = []
    for date, tobs, station in past_year_tobs_qry:
        tobs_dict = {}
        tobs_dict["date"] = date
        tobs_dict["tobs"] = tobs
        tobs_dict["station"] = station
    tobs_list.append(tobs_dict)

    return jsonify(tobs)

@app.route("/api/v1.0/<start>")
#  
def start_date(start):
    session = Session(engine) 

    """Return a JSON list of the minimum temperature, the average temperature, and the max temperature for a given start date."""

    # Create query for minimum, average, and max tobs where query date is greater than or equal to the date the user submits in URL
    start_tobs = session.query(func.min(measurement.tobs),func.avg(measurement.tobs),func.max(measurement.tobs)).\
        filter(measurement.date >= start).all()
    
    session.close() 

    # Create a list of min,max,and average temps that will be appended with dictionary values for min, max, and avg tobs queried above
    start_date_tobs_values =[]
    for min, avg, max in start_tobs:
        start_date_tobs_dict = {}
        start_date_tobs_dict["min"] = min
        start_date_tobs_dict["average"] = avg
        start_date_tobs_dict["max"] = max
        start_date_tobs_values.append(start_date_tobs_dict)
    
    return jsonify(start_date_tobs_values)

# Create a route that when given the start date only, returns the minimum, average, and maximum temperature observed for all dates greater than or equal to the start date entered by a user

@app.route("/api/v1.0/<start>/<end>")

# Define function, set start and end dates entered by user as parameters for start_end_date decorator
def Start_end_date(start, end):
    session = Session(engine)

    """Return a list of min, avg and max tobs between start and end dates entered"""
    
    # Create query for minimum, average, and max tobs where query date is greater than or equal to the start date and less than or equal to end date user submits in URL

    start_end_date_tobs_results = session.query(func.min(measurement.tobs), func.avg(measurement.tobs), func.max(measurement.tobs)).\
        filter(measurement.date >= start).\
        filter(measurement.date <= end).all()

    session.close()
  
    # Create a list of min,max,and average temps that will be appended with dictionary values for min, max, and avg tobs queried above
    tobs_date_values = []
    for min, avg, max in start_end_date_tobs_results:
        tobs_date_dict = {}
        tobs_date_dict["min_temp"] = min
        tobs_date_dict["avg_temp"] = avg
        tobs_date_dict["max_temp"] = max
        tobs_date_values.append(tobs_date_dict) 
    

    return jsonify(tobs_date_values)
   
if __name__ == '__main__':
    app.run(debug=True) 
