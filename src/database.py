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
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics(
                        id SERIAL PRIMARY KEY,
                        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        cpu_usage REAL,
                        memory_usage REAL,
                        disk_usage REAL,
                        network_mbps REAL
                    );
                """)
                connection.commit()
                try:
                    cursor.execute("ALTER TABLE system_metrics ADD COLUMN network_mbps REAL;")
                except:
                    connection.rollback() # Column already exists
                
                connection.commit()
            connection.close()
            print("!!! Database Schema Ready !!!")
    
    def save_metric(self, cpu, memory, disk, network):
        connection = self._get_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO system_metrics (cpu_usage, memory_usage, disk_usage, network_mbps)" \
                        "VALUES (%s, %s, %s, %s)",
                        (cpu, memory, disk, network)
                    )
                    connection.commit()
            except Exception as e:
                print(F"Save to DB Failed: {e}")
            finally:
                connection.close()
    
    def get_recent_metrics(self, limit=10):
        """
        Retreives the last 'limit' entries from the DB
        """
        connection = self._get_connection()
        clean_data = []

        if connection:
            try:
                with connection.cursor() as cursor:
                    # Ordered by newest first
                    cursor.execute("""
                        SELECT timestamp, cpu_usage, memory_usage, disk_usage, network_mbps
                        FROM system_metrics
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """, (limit,))
                    data = cursor.fetchall()

                    for row in data:
                        clean_data.append({
                            "timestamp": row[0].isoformat(),
                            "cpu": row[1],
                            "memory": row[2],
                            "disk": row[3],
                            "network": row[4]
                        })
            except Exception as e:
                print(f"Fetching recent metrics Failed: {e}")
            finally:
                connection.close()
        
        return clean_data