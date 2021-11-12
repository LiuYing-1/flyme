from typing import List
from flask import Flask
from flask import request
from datetime import datetime
from data import Flight
import json
import pymysql
from werkzeug.wrappers import response
app = Flask(__name__)


# Azure Database Connection - Cloud
def conn():
    database = pymysql.connect(host="ooxzzs27.2402.dnstoo.com", 
                               port=5503,
                               user="w31wnp_f",
                               password="XEGXR20210511135626",
                               db="w31wnp")    
    return database


# Extract Values and assign them, respectively
def extractValues(result):
    items = []
    for flight in result:
        fid = flight[0]
        code = flight[1]
        startRegion = flight[2]
        endRegion = flight[3]
        departureTime = str(flight[4])
        landingTime = str(flight[5])
        price = flight[6]

        # item = {"id": fid, "code": code, "startRegion": startRegion, "endRegion": endRegion, "departureTime": departureTime, "landingTime": landingTime, "price": price}
        item = "{}:{} - {}({}) => {}({}), RMB: {}".format(fid, code, startRegion, departureTime, endRegion, landingTime, price)
        items.append(item)
    return items


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
