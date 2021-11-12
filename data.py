from pydantic import BaseModel
from datetime import datetime
import pymysql

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
    
    
if __name__ == "__main__":
    
    connection = pymysql.connect(host="flymedb.mysql.database.azure.com", 
                              user="yiliu18@flymedb",
                              password="202181224_Njit",
                              db="flymetest")
      
    with connection:
        with connection.cursor() as cursor:
            sql = "select * from flight"
            cursor.execute(sql)
            result = cursor.fetchone()
            print(Flight.create_from_tuple(result).json())
        
