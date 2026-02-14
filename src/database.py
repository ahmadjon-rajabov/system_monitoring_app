import psycopg2
import os 
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.host = "localhost"
        self.name = os.getenv("POSTGRES_DB")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.connection = None
        self._initialize_tables()
    
    def _get_connection(self):
        """        
        Private method: Creates a new connection
        """
        try:
            return psycopg2.connect(
                host = self.host,
                database = self.name,
                user = self.user,
                password = self.password
            )
        except Exception as e:
            print(f"DB Connection Error: {e}")
            return None
    
    def _initialize_tables(self):
        """
        Private method: Set up the table if missing
        """
        connection = self._get_connection()
        if connection:
            with connection.cursor() as cursor:
                # added disk_usage to the schema here
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics(
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL
                    );
                """)
                connection.commit()
            connection.close()
            print("!!! Database Table Ready !!!")
    
    def save_metric(self, cpu, memory, disk):
        connection = self._get_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO system_metrics (cpu_usage, memory_usage, disk_usage)" \
                        "VALUES (%s, %s, %s)",
                        (cpu, memory, disk)
                    )
                    connection.commit()
            except Exception as e:
                print(F"Save to DB Failed: {e}")
            finally:
                connection.close()