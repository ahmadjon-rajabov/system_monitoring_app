import os, platform, psutil
import google.generativeai as genai
from dotenv import load_dotenv
from src.database import DatabaseManager
from src.actuator import Actuator

class RagAgent:
    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.db = DatabaseManager()
        self.actuator = Actuator()

        if not self.api_key:
            print("!!! No Gemini API Key found is .env !!!")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-2.5-flash')
            except Exception as e:
                print(f"Error configuring Gemini: {e}")
                self.model = None
        
        self.system_architecture = """
        [SYSTEM ARCHITECTURE]
        - Project Name: System Monitor
        - Backend: Python FastAPI (Asynchronous)
        - Frontend: React + Vite + Recharts (Dark Mode Dashboard)
        - Database: PostgreSQL (Dockerized)
        - AI Models: Linear Regression, Random Forest, Gradient Boosting (Scikit-Learn)
        - Infrastructure: Docker Compose with Nginx (Web Server)
        - Orchestration: Custon Python Auto-Scaler & Actuator
        """
                
    def ask(self, user_question):
        """
        RAG Loop:
        1. Get Context (Recent DB Metrics)
        2. Combine with Question
        3. Ask Gemini
        """
        if not self.model:
            return "Error: Gemini API missing (Check .env file)"
        
        try:
            active_containers = self.actuator.get_container_count()
        except:
            active_containers = "Can't identify number of Nginx container. Docker Error"
        
        
        system_os = platform.system()
        disk_path = '/'

        if system_os == 'Windows':
            disk_path = 'C:\\'
        elif system_os == 'Darwin':
            if os.path.exists('/System/Volumes/Data'):
                disk_path = '/System/Volumes/Data'
        
        try:
            disk_info = psutil.disk_usage(disk_path)
        except Exception as e:
            print(f"Disk check failed for {disk_path}, falling back to current directory")
            disk_info = psutil.disk_usage('.')
        
        # Hardware context
        memory = psutil.virtual_memory()
        hardware_info = f"""
        [HARDWARE SPECS]
        - Hostname: {platform.node()}
        - OS: {platform.system()} {platform.release()}
        - CPU Arch: {platform.machine()}
        - CPU Cores: {psutil.cpu_count(logical=True)}
        - Total RAM: {round(memory.total / (1024 ** 3), 2)} GB
        - Total Disk: {round(disk_info.total / (1024 ** 3), 2)} GB
        - Disk Used: {round(disk_info.used / (1024 ** 3), 2)} GB
        """
        infra_info = f"""
        [INFRASTRUCTURE STATUS]
        - Active Nginx Web Servers: {active_containers}
        - Orchestrator: Docker Compose
        """
        
        # 24h Summary
        summary = self.db.get_24h_summary()
        history_context = "No historical data available"
        if summary:
            history_context = f"""
            [LAST 24 HOURS SUMMARY]
            - Data Points Collected: {summary.get('data_points')}
            - CPU Load: Min {summary.get('cpu_min')}%, Max {summary.get('cpu_max')}%, Avg {summary.get('cpu_avg')}%
            - Memory Usage: Min {summary.get('mem_min')}%, Max {summary.get('mem_max')}%, Avg {summary.get('mem_avg')}%
            - Network Traffic: Max {summary.get('net_max')} MB/s, Avg {summary.get('net_avg')} MB/s
            """

        # Recent logs
        recent_data = self.db.get_recent_metrics(limit = 20)    # Fetch 60 rows, assuming 1 row every 5-10 sec
        logs_context = "[CURRENT LIVE METRICS (Last 30 seconds)]\n"
        for row in recent_data:
            logs_context += f"- Time: {row['timestamp']}, CPU: {row['cpu']}%, Network: {row['network']} MB/s\n"
        
        # Augmentation
        prompt = f"""
        You are 'System Monitoring', an expert Site Reliability Engineer (SRE)/DevOps AI assistant running on {platform.node()}.
        Analyze the system metrics below to answer the user's question.

        [SYSTEM CONTEXT]
        {self.system_architecture}
        {hardware_info}
        {infra_info}
        {history_context}
        {logs_context}

        [USER QUESTION]
        {user_question}

        [INSTRUCTIONS]
        - Use the HARDWARE SPECS to answer questions about disk/RAM size.
        - Use the 24H SUMMARY to answer questions about "yesterday" or "general health".
        - Use CURRENT LIVE METRICS to answer "now".
        - If the user asks about something older than 24 hours, apologize and say you only track 24 hours.
        - You have permission to control the infrastructure. 
            - If the user explicitly asks to "Scale Up" or "Add Server", output EXACTLY: [ACTION: SCALE_UP]
            - If the user explicitly asks to "Scale Down" or "Remove Server", output EXACTLY: [ACTION: SCALE_DOWN]
        - Be concise and professional. No fluff. Structure the answer like a status report
        """

        try:
            response = self.model.generate_content(prompt)
            reply = response.text.strip()

            if "[ACTION: SCALE_UP]" in reply:
                self.actuator.scale_up()
                return "**Command Executed:** I have successfully scaled UP the Nginx/Client server"
            elif "ACTION: SCALE_DOWN" in reply:
                self.actuator.scale_down()
                return "**Command Executed:** I have successfully scaled DOWN the Nginx/Client server"
            
            return reply
        except Exception as e:
            return f"AI Generation Error: {str(e)}"

if __name__ == "__main__":
    agent = RagAgent()
    print("Asking Gemini...")
    print(agent.ask("Why is the CPU so high right now?"))
