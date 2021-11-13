import os
import json
import random
import pymysql
from data import Flight, User, Ticket
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
def getFlightByFlightCode(code, cursor):
    sql = "select * from flight where flight_code = '{}'".format(code)
    cursor.execute(sql)
    result = cursor.fetchone()
    
    return result

# Generate ticketCode
def generateTicketCode():
    str = ""
    for i in range(5):
        ch = chr(random.randrange(ord('1'), ord('9') + 1))
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
    passwordFromDatabase = user[2]
    
    # Get corresponding flight.id => FlightInformation
    flight = getFlightByFlightCode(flightCode, cur)
    flightId = flight[0]
    
    # Confirm the ticket - Insert the value of ticket
    if password == passwordFromDatabase:
        ticketCode = int(generateTicketCode())
        sqlStatement = "insert into user_ref_flight(flight_id, user_id, ticket_code) values('{}', '{}', '{}')".format(flightId, userId, ticketCode)
        cur.execute(sqlStatement)
        message = "Your ticket has been booked successfully, ticket code is '{}'".format(ticketCode)
    else:
        message = "Your password is incorrect, please restart this branch of the conversation."
    response = {"messages":message}
    
    return response

# Book Tickets => Business 2
def bookTickets(paramsFromAssistant, cur):
    step = paramsFromAssistant["signal"]
    if(step == "first"):
        response = bookTicketsFirstStepCheck(paramsFromAssistant, cur)
    elif(step == "second"):
        response = bookTicketsSecondStepBook(paramsFromAssistant, cur)
    
    return response

# Check the existence of the ticket by ticket code
def getTicketByTicketCode(code, cur):
    sql = "select * from user_ref_flight where ticket_code = '{}'".format(code)
    cur.execute(sql)
    result = cur.fetchone()
    
    return result

# Validate the corresponding user information of the ticket
def validateUserOfTicketByTicketCode(username, password, code, cur):
    sql = "select \
                user.username, user.password \
            from \
                user, user_ref_flight \
            where \
                user.id = user_ref_flight.user_id \
            and \
                ticket_code='{}'".format(code)
    cur.execute(sql)
    result = cur.fetchone()
    
    usernameFromDatabase = result[0]
    passwordFromDatabase = result[1]
    
    if (usernameFromDatabase != username or passwordFromDatabase != password):
        return False
    else:
        return True
    
# Get ticket details
def getTicketInDetailByTicketCode(code, cur):
    sql = "select\
                user_ref_flight.ticket_code, \
	            user.username, \
	            user.password, \
	            flight.flight_code, \
	            flight.departure_time, \
	            flight.price \
           from \
	            user, flight, user_ref_flight \
           where \
	            user.id = user_ref_flight.user_id \
           and \
	            flight.id = user_ref_flight.flight_id \
           and \
	            ticket_code='{}'".format(code)
    cur.execute(sql)
    result = cur.fetchone()
    
    return result

# Check Tickets => Business 3
def checkTickets(paramsFromAssistant, cur):
    # Assign the values from assistant to each variables
    usernameFromAssistant = paramsFromAssistant["username"]
    passwordFromAssistant = paramsFromAssistant["password"]
    ticketCodeFromAssistant = paramsFromAssistant["ticketCode"]
    
    # Check the ticket code and validate the user
    ticket = getTicketByTicketCode(ticketCodeFromAssistant, cur)
    
    # Initialize the existence
    existence = "no"
    if ticket == None:
        message = "Sorry, Ticket Code '{}' does not exist. Please restart this branch of the conversation".format(ticketCodeFromAssistant)
    else:
        result = validateUserOfTicketByTicketCode(usernameFromAssistant, \
                                                  passwordFromAssistant, \
                                                  ticketCodeFromAssistant, cur)
        
        # Initialize the message
        message = "Sorry, incorrect user information. Please restart this branch of the conversation."
        
        if result:
            existence = "yes"
            res = getTicketInDetailByTicketCode(ticketCodeFromAssistant, cur)
            message = Ticket.create_from_tuple(res).json()
    response = {"messages": message, "mark": existence}
    
    return response

# Calculate the criteria
def getCriteria():
    value1 = datetime(2021, 11, 13, 0, 0, 0).timestamp()
    value2 = datetime(2021, 11, 15, 0, 0, 0).timestamp()
    return value2-value1

# Delete the ticket
def deleteTicketByTicketCode(code, cur):
    sql = "delete from user_ref_flight where ticket_code='{}'".format(code)
    cur.execute(sql)


# Result mark value is yes
def resMarkIsValue(res, cur):
    ticket = json.loads(res["messages"])

    # Get the departure_time, price and flight_code
    departure_time = ticket["departure_time"]
    ticketCode = ticket["ticket_code"]
    flightCode = ticket["flight_code"]
    price = ticket["price"]
    
    # Delete the ticket
    deleteTicketByTicketCode(ticketCode, cur)
    
    # Divide the time
    year = int(departure_time[0:4])
    month = int(departure_time[5:7])
    day = int(departure_time[8:10])
    hour = int(departure_time[11:13])
    minute = int(departure_time[14:16])
    sec = int(departure_time[17:19])
    
    # Convert the departure_time into 'timestamp'
    timestampOfDepartureTime = datetime(year, month, day, hour, minute, sec).timestamp()
    now = (datetime.now()).timestamp()
    
    # Compare the remaining time with the criteria
    remaining = timestampOfDepartureTime - now
    criteria = getCriteria()
    
    if(remaining > criteria):
        fee = price * 1
    else:
        fee = price * 0.9

    message = "Your ticket '{}' of '{}' has been cancelled with returning fee '{}' => ('{}')".format(ticketCode, flightCode, fee, price)
    return message


# Cancel Tickets => Business 4
def cancelTickets(paramsFromAssistant, cur):
    # Repeat the checkTickets() Operation, as they share the same logic
    # Return the ticket for further operation
    result = checkTickets(paramsFromAssistant, cur)
    
    if (result["mark"] == "yes"):
        message = resMarkIsValue(result, cur)
    elif (result["mark"] == "no"):
        message = "This ticket does not exist. Please restart this branch of this conversation."
    
    response = {"messages": message}
    
    return response

# Give scores for the service => Business 5
def giveFeedback(paramsFromAssistant, cur):
    # Assign the values to username and remark
    username = paramsFromAssistant["username"]
    remark = paramsFromAssistant["remark"]
    
    # Insert Operation
    sql = "insert into feedback(username, remark) values('{}', '{}')".format(username, remark)
    cur.execute(sql)
    
    message = "Thanks for your advice to FlyMe! \
               Hope to offer you with a better experience next time!"
               
    response = {"messages": message}
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
        
    elif action == "checkTickets":
        messages = checkTickets(params, cursor)

    # Cancel Tickets Part
    elif action == "cancelTickets":
        messages = cancelTickets(params, cursor)
        
    # Collect Feedback Part
    elif action == "giveFeedback":
        messages = giveFeedback(params, cursor)

    # Commit the change
    flymeDB.commit()
    # Close Connection
    flymeDB.close()
    # return params
    return messages

# Dev Doc - Liu, Ying
@app.route("/static/doc")
def devDoc():
    return app.send_static_file('doc.html')

# Cancellation Terms - FlyMe Airline (Liu, Ying)
@app.route("/static/cancellation")
def cancellationTerms():
    return app.send_static_file('cancellation.html')

# Static Index Here
@app.route("/")
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run()
