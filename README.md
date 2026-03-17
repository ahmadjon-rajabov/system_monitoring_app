# System Monitoring App: AI-Powered DevOps Command Center
![Status](https://img.shields.io/badge/Status-Active-brightgreen)
![Docker](https://img.shields.io/badge/Docker-Supported-blue)
![Kubernetes](https://img.shields.io/badge/Kubernetes-Supported-326ce5)
![AI](https://img.shields.io/badge/AI-Gemini_3.1_Pro-orange)

<div align="center">
  <img src="dashboard.png" alt="System Monitoring App Dashboard" width="100%">
</div>

**System Monitor** is an autonomous, self-healing Infrastructure-as-a-Service (IaaS) platform. It monitors system resources in real-time, predicts future traffic loads using Machine Learning, and autonomously scales containerized applications to meet demand. It features a built-in RAG (Retrieval-Augmented Generation) AI agent that acts as a virtual Site Reliability Engineer (SRE), capable of interpreting live metrics and executing infrastructure commands via a natural language chat interface.

## ✨ Core Features
*   📊 **Real-Time Telemetry:** Collects and visualizes CPU, Memory, Disk, and Network traffic (KB/s) with a React/Recharts dashboard.
*   🧠 **Predictive AI Scaling:** Utilizes an arena of Scikit-Learn models (Linear Regression, Random Forest, Gradient Boosting) to forecast upcoming network and compute loads.
*   🤖 **Autonomous Autoscaler:** A background daemon that dynamically scales Nginx replica clusters up/down based on live network traffic thresholds.
*   🎚️ **State Management (Auto/Manual Override):** Real-time database-backed toggle allowing operators to pause the autonomous agent and assume manual control.
*   💬 **AI SRE Chatbot (RAG):** Integrated Gemini 3.1 LLM contextually aware of the hardware host, historical 24h database summaries, and live logs. It can execute physical Docker/K8s scaling commands via chat.
*   🐳 **Hybrid Orchestration:** Fully decoupled code designed to run seamlessly on a local **Docker Compose** sandbox OR on cloud **Kubernetes (K3s)** cluster.

## 🏗️ Architecture & Tech Stack
*   **Frontend:** React.js, Vite, Recharts, Lucide Icons.
*   **Backend:** Python 3.12, FastAPI, Uvicorn.
*   **Data & AI:** PostgreSQL, Scikit-Learn, Pandas, Google Generative AI (Gemini).
*   **DevOps & Automation:** Docker, Docker Compose, Kubernetes (K3d/K3s), Kubectl, Psutil.

## 🚀 Getting Started
### Prerequisites
*   [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
*   A [Google Gemini API Key](https://aistudio.google.com/app/apikey).

### 1. Configuration
Clone the repository and set up your environment variables:
```bash
git clone https://github.com/YOUR_USERNAME/system_monitoring_app.git
cd system_monitoring_app
```

#### Copy the example env file and insert your API Key
```bash
cp .env.example .env
```

### 2. Choose Your Orchestrator
System supports two deployment targets. Choose one:

**Option A:** Docker Sandbox (Recommended for quick testing). This mode runs the entire stack, including the background agents, in pure Docker Compose. Ensure `ORCHESTRATOR=docker` is set in your `.env`.
```bash
docker compose up -d --build
```

<br>

**Option B:** Kubernetes Cluster (K3d). This mode deploys the stack using Kubernetes manifests, simulating a highly available cloud environment.
```bash
# Create the virtual cluster with a load balancer on port 8081
k3d cluster create eco-cluster --api-port 6550 -p "8081:80@loadbalancer" --agents 2

# Build the images
docker build -t system-monitor-backend:v1 -f Dockerfile.backend .
docker build -t system-monitor-frontend:v1 -f Dockerfile.frontend .

# Import images into the cluster
k3d image import system-monitor-backend:v1 system-monitor-frontend:v1 -c system-monitor-cluster

# Apply manifests (Secrets, PVCs, Deployments, Services, Ingress, RBAC)
kubectl apply -f k8s/
```

## 🎮 How to Use the Command Center
1. **Access the Dashboard:**
    - If using Docker: http://localhost:5173
    - If using Kubernetes: http://localhost:8081
2. **Monitor Traffic:** Watch the Network graph. The Autoscaler will automatically add Nginx replicas if traffic exceeds 2 MB/s and remove them when idle.
3. **Command the AI:**
    - Toggle the switch at the top right to **Manual Mode**.
    - Open the Chat Widget.
    - Type: *"Scale up the web server please."*
    - The AI will process the intent and execute a physical scaling command against the Docker Socket / K8s API.

## 🧪 Simulating Network Load
To trigger an automatic scale-up event, generate dummy network traffic inside the monitor container:

**Docker Mode:**
```bash
docker exec -it system-monitor-agent /bin/sh -c "while true; do curl -o /dev/null -s http://speedtest.tele2.net/100MB.zip; sleep 1; done"
```

**Kubernetes Mode:**
```bash
kubectl exec -it deploy/monitor-deployment -- /bin/sh -c "while true; do curl -o /dev/null -s http://speedtest.tele2.net/100MB.zip; sleep 1; done"
```
*Press Ctrl+C to stop the traffic and watch the system automatically scale back down.*

## 🛣️ Future Roadmap
- **CI/CD Pipeline:** Automated testing and Docker image publishing via GitHub Actions/GitLab.
- **Vector Database Integration:** Incorporating ChromaDB to give the AI agent contextual knowledge of official Kubernetes/Docker documentation.
- **Infrastructure as Code:** Ansible playbooks for automated host provisioning.

