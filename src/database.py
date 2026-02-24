import psycopg2
import os 
from dotenv import load_dotenv

class DatabaseManager:
    def __init__(self):
        load_dotenv()
        self.host = os.getenv("POSTGRES_HOST", "localhost")
        self.name = os.getenv("POSTGRES_DB")
        self.user = os.getenv("POSTGRES_USER")
        self.password = os.getenv("POSTGRES_PASSWORD")
        self.connection = None
        self._initialize_tables()
    
    def get_connection(self):
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
        connection = self.get_connection()
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
        connection = self.get_connection()
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
        connection = self.get_connection()
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
    
    def get_24h_summary(self):
        """
        Calculatees Highs, Lows, and Averages for the last 24 hours
        """
        connection = self.get_connection()
        summary = {}

        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        SELECT MIN(cpu_usage), MAX(cpu_usage), AVG(cpu_usage),
                            MIN(memory_usage), MAX(memory_usage), AVG(memory_usage),
                            MIN(network_mbps), MAX(network_mbps), AVG(network_mbps),
                            COUNT(*)
                        FROM system_metrics
                        WHERE timestamp > NOW() - INTERVAL '24 hours'
                    """)
                    row = cursor.fetchone()
                    if row and row[9] > 0: # Is there data
                        summary = {
                            "cpu_min": row[0], "cpu_max": row[1], "cpu_avg": round(row[2], 2),
                            "mem_min": row[3], "mem_max": row[4], "mem_avg": round(row[5], 2),
                            "net_min": row[6], "net_max": row[7], "net_avg": round(row[8], 2),
                            "data_points": row[9]
                        }
            except Exception as e:
                print(f"Summary 24h fetch failed: {e}")
            finally:
                connection.close()
        return summary