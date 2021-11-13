import os
import pymysql
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

# Flight Class
class Flight(BaseModel):
    id: int
    flight_code: str
    start_region: str
    end_region: str
    departure_time: datetime
    landing_time: datetime
    price: float
    
    @classmethod
    def create_from_tuple(cls, args):
        return cls(**{key: args[i] for i, key in enumerate(Flight.__fields__.keys())})
    
# User Class
class User(BaseModel):
    id: int
    username: str
    password: str
    
    @classmethod
    def create_from_tuple(cls, args):
        return cls(**{key: args[i] for i, key in enumerate(User.__fields__.keys())})

# Middle Class
class Middle(BaseModel):
    flight_id: int
    user_id: int
    ticket_code: int

    @classmethod
    def create_from_tuple(cls, args):
        return cls(**{key: args[i] for i, key in enumerate(Middle.__fields__.keys())})


# Ticket Class
class Ticket(BaseModel):
    ticket_code: int
    username: str
    password: str
    flight_code: str
    departure_time: datetime
    price: float    
    
    @classmethod
    def create_from_tuple(cls, args):
        return cls(**{key: args[i] for i, key in enumerate(Ticket.__fields__.keys())})
    
# Test Part
load_dotenv()
host = os.getenv("HOST")
port = int(os.getenv("PORT"))
user = os.getenv("DATABASEUSER")
password = os.getenv("PASSWORD")
db = os.getenv("DB")

if __name__ == "__main__":
    
    connection = pymysql.connect(host=host, 
                              port=port,
                              user=user,
                              password=password,
                              db=db)
      
    with connection:
        with connection.cursor() as cursor:
            # Test class => Flight
            sql = "select * from flight"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(Flight.create_from_tuple(result).json())
            
            # Test class => User
            sql = "select * from user"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(User.create_from_tuple(result).json())
            
            # Test class => Middle
            sql = "select * from user_ref_flight"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(Middle.create_from_tuple(result).json())
            
            # Test class => Ticket
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
	                    flight.id = user_ref_flight.flight_id"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(Ticket.create_from_tuple(result).json())
