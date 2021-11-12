import os
import json
import random
import pymysql
from data import Flight, User
from typing import List
from flask import Flask
from flask import request
from datetime import datetime
from dotenv import load_dotenv
from werkzeug.wrappers import response

app = Flask(__name__)

load_dotenv()
host = os.getenv("HOST")
port = int(os.getenv("PORT"))
user = os.getenv("DATABASEUSER")
password = os.getenv("PASSWORD")
db = os.getenv("DB")

# Database Connection - Cloud
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


# Book Tickets - First Step
def bookTicketsFirstStepCheck(paramsFirstStep, cur):
    print("first step")
    # Assign the values as the searching conditions
    startRegion = paramsFirstStep["startRegion"]
    endRegion = paramsFirstStep["endRegion"]
    date = paramsFirstStep["date"]
    sqlStatement = "select * from flight where (start_region = '{}' and end_region = '{}' and departure_time like '{} %')".format(startRegion, endRegion, date)
    flights = get_flights(cur, sqlStatement)
    responseFirstStep = {
        "flights": [
            flight.dict() for flight in flights
        ]
    }
    return responseFirstStep

# Get corresponding user information with username
def getUserByUsername(name, cursor):
    sql = "select * from user where username = '{}'".format(name)
    cursor.execute(sql)
    result = cursor.fetchone()
    
    return result

# Get corresponding flight information with flightCode
def getFlightByFlightcode(code, cursor):
    sql = "select * from flight where flight_code = '{}'".format(code)
    cursor.execute(sql)
    result = cursor.fetchone()
    
    return result

# Generate ticketCode
def generateTicketCode():
    str = ""
    for i in range(5):
        ch = chr(random.randrange(ord('0'), ord('9') + 1))
        str += ch
    return str

# Book Tickets - Second Step
def bookTicketsSecondStepBook(paramsSecondStep, cur):
    print("second step")
    # Assign the flight code to the variable
    flightCode = paramsSecondStep["flightCode"]
    username = paramsSecondStep["username"]
    password = paramsSecondStep["password"]
    
    # Get corresponding user.id => UserInformation
    user = getUserByUsername(username, cur)
    userId = user[0]
    userName = user[1]
    passWord = user[2]
    
    # Get corresponding flight.id => FlightInformation
    flight = getFlightByFlightcode(flightCode, cur)
    flightId = flight[0]
    
    # Confirm the ticket - Insert the value of ticket
    if password == passWord:
        ticketCode = int(generateTicketCode())
        sqlStatement = "insert into user_ref_flight(flight_id, user_id, ticket_code) values('{}', '{}', '{}')".format(flightId, userId, ticketCode)
        cur.execute(sqlStatement)
        message = "Your ticket has been booked successfully, ticket code is '{}'".format(ticketCode)
    else:
        message = "Password Not Matching"
    response = {"message":message}
    
    return response

# Book Tickets => Business 2
def bookTickets(paramsFromAssistant, cur):
    print(len(paramsFromAssistant))
    step = paramsFromAssistant["signal"]
    if(step == "first"):
        response = bookTicketsFirstStepCheck(paramsFromAssistant, cur)
    elif(step == "second"):
        response = bookTicketsSecondStepBook(paramsFromAssistant, cur)
    
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

@app.route("/static/doc")
def devdoc():
    return app.send_static_file('doc.html')

# Static Index Here
@app.route("/")
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()
