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

        self.tables_ready = False
        self.initialize_tables()
    
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
        
    def get_config(self, key):
        self.ensure_table()
        connection = self.get_connection()
        val = None
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT value FROM system_config WHERE key = %s", (key,))
                    row = cursor.fetchone()
                    if row: val = row[0]    # string 'auto' from the tuple 
            finally:
                connection.close()
        return val
    
    def set_config(self, key, value):
        self.ensure_table()
        connection = self.get_connection()
        if connection:
            try:
                with connection.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO system_config (key, value) VALUES (%s, %s)
                        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value
                    """, (key, value))
                    connection.commit()
            finally:
                connection.close()

    def initialize_tables(self):
        """
        Private method: Set up the table if missing
        """
        connection = self.get_connection()
        if connection:
            try:
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
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS system_config (
                            key TEXT PRIMARY KEY,
                            value TEXT           
                        );
                    """)
                    cursor.execute("""
                        INSERT INTO system_config (key, value)
                        VALUES ('scaling_mode', 'auto')
                        ON CONFLICT (key) DO NOTHING;
                    """)
                    connection.commit()
                    # print("!!! Database Schema Ready !!!")
            except Exception as e:
                print(f"Table init failed: {e}")
            finally:
                connection.close()
    
    def ensure_table(self):
        """IF tables aren't ready, try to create them"""
        if not self.tables_ready:
            self.initialize_tables()
    
    def save_metric(self, cpu, memory, disk, network):
        self.ensure_table()
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
                if "releation" in str(e) and "does not exists" in str(e):
                    print("Tables missing. Resetting flag")
                    self.tables_ready = False
                print(F"Save to DB Failed: {e}")
            finally:
                connection.close()
    
    def get_recent_metrics(self, limit=10):
        """
        Retreives the last 'limit' entries from the DB
        """
        self.ensure_table()
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
        self.ensure_table()
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