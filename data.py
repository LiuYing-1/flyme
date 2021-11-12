import os
import pymysql
from pydantic import BaseModel
from datetime import datetime
from dotenv import load_dotenv

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
    

class User(BaseModel):
    id: int
    username: str
    password: str
    
    @classmethod
    def create_from_tuple(cls, args):
        return cls(**{key: args[i] for i, key in enumerate(User.__fields__.keys())})

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
            sql = "select * from flight"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(Flight.create_from_tuple(result).json())
            sql = "select * from user"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(User.create_from_tuple(result).json())
