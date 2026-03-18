import os, platform, psutil, chromadb
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
        
        self.chroma_host = os.getenv("CHROMA_HOST", "localhost")
        self.collection = None
        try:
            self.chroma_client = chromadb.HttpClient(host=self.chroma_host, port=8000)
            self.collection = self.chroma_client.get_or_create_collection(name="devops_runbook")
            self.seed_knowledge()
        except Exception as e:
            print(f"ChromaDB not reachable at {self.chroma_host}: {e}")

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
        
        rag_context = "No specific runbook documentation found"
        if self.collection:
            try:
                # find 2 most relevant documents 
                results = self.collection.query(query_texts=[user_question], n_results=2)
                if results['documents'] and results['documents'][0]:
                    rag_context = "\n".join(results['documents'][0])
                    print(f"CHROMA FOUND THIS CONTEXT: {rag_context}", flush=True)
            except Exception as e:
                print(f"Chroma Query Error: {e}")

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
        
        current_mode = self.db.get_config("scaling_mode") or "auto"

        # Augmentation
        prompt = f"""
        You are 'System Monitoring', an expert Site Reliability Engineer (SRE)/DevOps AI assistant running on {platform.node()}.
        Analyze the system metrics below to answer the user's question.
        
        [CURRENT OPERATING MODE]
        {current_mode}

        [SYSTEM CONTEXT]
        {self.system_architecture}
        
        [VECTOR KNOWLEDGE BASE (RUNBOOK)]
        {rag_context}

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
        - If the user asks a technical or troubleshooting question, heavily prioritize the [VECTOR KNOWLEDGE BASE] to answer it.
        - If the user asks about something older than 24 hours, apologize and say you only track 24 hours.
        - You have permission to control the infrastructure. 
            - If the user explicitly asks to "Scale Up" or "Add Server", output EXACTLY: [ACTION: SCALE_UP]
            - If the user explicitly asks to "Scale Down" or "Remove Server", output EXACTLY: [ACTION: SCALE_DOWN]
            - If user asks to Scale Up/Down AND moode is 'auto': REFUSE the command. Tell them: "I cannot execute commands in Auto Mode. Please switch to Manual Mode
            - IF user asks to Scale Up/Down AND mode is 'manual': Output: [ACTION: SCALE_UP] or [ACTION: SCALE_DOWN]
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

def seed_knowledge(self):
    """Injecfts technical manuals into the Vector Database"""
    docs = [
        "If a Kubernetes Pod is stuck in 'CrashLoopBackOff', it means the application inside the container is repeatedly crashing. To fix it, check the logs using: kubectl logs deploy/<deployment-name> --previous",
        "If a Kubernetes Pod is stuck in 'ErrImageNeverPull', it means the imagePullPolicy is set to 'Never' but the node does not have the image locally. To fix it, import the image using 'k3d image import' or change the policy to 'IfNotPresent'.",
        "A '502 Bad Gateway' error from the Kubernetes LoadBalancer usually means the worker node is frozen or the backend service is misconfigured in the Ingress.",
        "System Monitor Auto-Scaler logic: High Network Traffic is usually above 2 MB/s. Low traffic is below 100 KB/s."
    ]

    # ChromaDB needs a unique ID for every document
    ids = [f"runbook_rule_{i}" for i in range(len(docs))]   # 'upsert' safely inserts or updates 
    self.collection.upsert(documents=docs, ids=ids)
    print("ChromaDB Knowledge Base Seeded!")

if __name__ == "__main__":
    agent = RagAgent()
    print("Asking Gemini...")
    print(agent.ask("Why is the CPU so high right now?"))
