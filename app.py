from typing import List
from flask import Flask
from flask import request
from datetime import datetime
from data import Flight
from dotenv import load_dotenv
import os
import json
import pymysql
from werkzeug.wrappers import response
app = Flask(__name__)

load_dotenv()
host = os.getenv("HOST")
port = int(os.getenv("PORT"))
user = os.getenv("DATABASEUSER")
password = os.getenv("PASSWORD")
db = os.getenv("DB")

# Azure Database Connection - Cloud
def conn():
    database = pymysql.connect(host=host, 
                               port=port,
                               user=user,
                               password=password,
                               db=db)
    return database


# Convert Response into JSON format
def convertFormat(items):
    flights = {"flights": items}
    res = json.loads(json.dumps(flights))
    print(type(res))
    print(res)
    return res


def get_flights(cursor, sql) -> List[Flight]:
    # View all the records in the table 'flight'
    cursor.execute(sql)
    resultSet = cursor.fetchall()
    flights = [
        Flight.create_from_tuple(result) for result in resultSet
    ]
    return flights


# View Flights Information => Business 1
def viewFlights(cur):
    sqlStatement = "select * from flight"
    flights = get_flights(cur, sqlStatement)
    response = {
        "flights": [
            flight.dict() for flight in flights
        ]
    }
    
    return response


# Book Tickets => Business 2
def bookTickets(paramsFromAssistant, cur):
    # Assign the values as the searching conditions
    startRegion = paramsFromAssistant["startRegion"]
    endRegion = paramsFromAssistant["endRegion"]
    date = paramsFromAssistant["date"]
    
    sqlStatement = "select * from flight where (start_region = '{}' and end_region = '{}' and departure_time like '{} %')".format(startRegion, endRegion, date)


    flights = get_flights(cur, sqlStatement)
    response = {
        "flights": [
            flight.dict() for flight in flights
        ]
    }
    
    print(paramsFromAssistant)
    
    return response


# Webhook Operations Here => http:webhook.flyme.social
@app.route("/webhook", methods=['POST', 'GET'])
def webhook():
    messages = ''
    # Connect the database and process the params
    flymeDB = conn()
    cursor = flymeDB.cursor()
    params = json.loads(request.data.decode('utf-8'))
    
    # Select which one to go
    action = params['action']

    # View Flights Part
    if action == 'viewFlights':
        messages = viewFlights(cursor)

    # Book Tickets Part
    elif action == "bookTickets":
        messages = bookTickets(params, cursor)

    # Close Connection
    flymeDB.close()
    # return params
    return messages

# Static Index Here
@app.route("/")
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()
