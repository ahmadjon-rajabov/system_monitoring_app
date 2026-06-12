# System Monitoring App: AI-Powered DevOps Command Center

<div align="center">
    <img src="dashboard.png" alt="System Monitoring App Dashboard" width="100%">
</div>

**System Monitor** is an autonomous, self-healing Infrastructure-as-a-Service (IaaS) platform. It monitors system resources in real-time, predicts future traffic loads using Machine Learning, and autonomously scales containerized applications. 

Beyond standard observability, it features a built-in **RAG (Retrieval-Augmented Generation) AI agent** that acts as a virtual Site Reliability Engineer (SRE). This agent interprets live metrics, reads DevOps runbooks, and executes infrastructure commands via a natural language chat interface.

## Project Structure

```text
system_monitoring_app/
├── .github/workflows/       # CI/CD pipelines (Quality Gates & Docker builds)
├── ansible/                 # Infrastructure as Code (Provisioning)
├── dashboard/               # React/Vite Frontend UI
├── k8s/                     # Kubernetes Manifests (Deployments, Services, RBAC)
├── src/                     # Core Python Backend
│   ├── actuator.py          # Executes physical scaling (Docker/K8s APIs)
│   ├── api.py               # FastAPI backend routing
│   ├── autoscaler.py        # Autonomous decision engine 
│   ├── database.py          # PostgreSQL connection & data pipeline
│   ├── monitor.py           # Telemetry ingestion daemon
│   ├── predictor.py         # Scikit-Learn Machine Learning models
│   └── rag_agent.py         # Gemini LLM + ChromaDB integration
├── tests/                   # QA & Automated Testing Suite
│   ├── test_api.py          # FastAPI route testing using TestClient & Mocks
│   ├── test_autoscaler.py   # Core logic unit tests with Pytest Mocking
│   └── test_integration.py  # E2E Database tests with Testcontainers
├── pyproject.toml           # Modern package management & tool config (uv, pytest, ruff)
└── docker-compose.yml       # Local sandbox orchestration
```

## Core Features

* **Real-Time Telemetry:** Collects and visualizes CPU, Memory, Disk, and Network traffic (KB/s) with a React/Recharts dashboard.
* **Predictive AI Scaling:** Utilizes an arena of Scikit-Learn models (Linear Regression, Random Forest, Gradient Boosting) to forecast upcoming network and compute loads.
* **Autonomous Autoscaler:** A background daemon that dynamically scales Nginx replica clusters up/down based on live network traffic thresholds.
* **State Management (Auto/Manual Override):** Real-time database-backed toggle allowing operators to pause the autonomous agent and assume manual control.
* **AI SRE Chatbot (RAG):** Integrated Gemini 2.5 LLM contextually aware of the hardware host, historical 24h database summaries, and live logs. It can execute physical Docker/K8s scaling commands via chat.
* **Hybrid Orchestration:** Fully decoupled code designed to run seamlessly on a local **Docker Compose** sandbox OR on cloud **Kubernetes (K3s)** cluster.

## System Architecture & Data Flow

System Monitoring is built using a decoupled, microservices architecture designed to run on both single-node Docker environments and multi-node Kubernetes clusters.

### 1. The Telemetry Pipeline (Observability)

A background Python daemon (`monitor.py`) continuously polls the host system and container network interfaces using `psutil`. This raw telemetry (CPU, RAM, Disk, Network KB/s) is ingested into a **PostgreSQL** database every second, creating a robust time-series dataset.

### 2. The AI & Knowledge Base (RAG via ChromaDB)

The "Brain" of the system relies on **Google's Gemini 2.5 Flash** LLM. To prevent hallucinations and provide accurate technical support, the system uses a **ChromaDB Vector Database**.

* **Ingestion:** On startup, technical DevOps runbooks and cluster rules are vectorized and stored in ChromaDB.
* **Retrieval:** When a user asks a question, the backend queries ChromaDB for relevant documentation and injects it into the LLM's prompt alongside the last 24 hours of PostgreSQL metrics.

### 3. The Control Loop (Autoscaler & Actuator)

An autonomous Python agent (`autoscaler.py`) evaluates the PostgreSQL metrics every 5 seconds.

* If network traffic exceeds **2 MB/s**, it triggers a `Scale Up` event. 
* If traffic drops below **50 KB/s**, it triggers a `Scale Down` event. 
* The **Actuator** class dynamically detects its environment. If running locally, it mounts `/var/run/docker.sock` to control Docker Compose. If running in K8s, it uses a dedicated `ServiceAccount` with RBAC permissions to patch Deployments via the Kubernetes API.

### 4. CI/CD Pipeline (GitHub Actions)

Upon pushing code to the `main` branch, **GitHub Actions** provisions a runner, builds the FastAPI Backend and React Frontend Docker images, and publishes them securely to the **GitHub Container Registry (GHCR)**.

## SDET & Quality Engineering

Utilized a modern Test Automation Pyramid, managed by uv (the ultra-fast Python package manager)

* **Unit Testing (The "Mocking Master"):** `pytest-mock` to intercept external dependencies, allowing us to test the `AutoScaler` logic against simulated high/low network traffic in milliseconds. Utilized FastAPI's `TestClient` to validate REST endpoints and routing logic without triggering the physical database or burning AI API credits.
* **Integration Testing (E2E with Testcontainers):** Avoided mocking the database layer. Instead, `testcontainers-python` dynamically spins up ephemeral, real PostgreSQL Docker containers on randomized ports. This proves the Python-to-SQL data pipeline functions flawlessly in a real environment before destroying the container.
* **Continuous Integration (CI/CD Quality Gates):** GitHub Actions enforces strict quality gates on every push. The pipeline automatically:
    1. Installs dependencies using `uv`.
    2. Runs `Ruff` to enforce formatting and catch unused variables/imports.
    3. Runs the Pytest suite, blocking deployment if *Test Coverage drops below 70%*. 
    4. Upon passing, builds and pushes Docker images to GHCR.

> **Note:** Coverage explicitly targets deterministic core logic like APIs, the Autoscaler, and DB Pipelines. Non-deterministic AI/LLM agents and hardware-level daemons are strategically omitted to prevent pipeline flakiness, adhering to modern SDET best practices

## Getting Started

### Prerequisites

* [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.
* A [Google Gemini API Key](https://aistudio.google.com/app/apikey).
* *Optional:* `uv` package manager for running local tests.

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

### 2. Local Testing & Quality Checks

Run the automated QA suite locally using uv:

```bash
uv sync                      # Installs dependencies
uv run ruff check .          # Runs the linter
uv run pytest tests/ -v -s   # Runs Unit and Integration tests
```

### 3. Deployment (Choose Your Orchestrator)

**Option A: One-Click Ansible Provisioning (Recommended).** Use the included Ansible playbook to automatically install dependencies, configure your machine, and launch the *Docker sandbox*.

```bash
ansible-playbook ansible/setup.yml
```

**Option B: Manual Docker Sandbox.** Runs the entire stack, including the background agents, in pure Docker Compose. Ensure `ORCHESTRATOR=docker` is set in your `.env`.

```bash
docker compose up -d --build
```

**Option C: Kubernetes Cluster (K3d).** Simulate a highly available cloud environment using the provided K8s manifests.

```bash
# Create the virtual cluster with a load balancer on port 8081
k3d cluster create system-monitor-cluster --api-port 6550 -p "8081:80@loadbalancer" --agents 2

# Build the images
docker build -t system-monitor-backend:v1 -f Dockerfile.backend .
docker build -t system-monitor-frontend:v1 -f Dockerfile.frontend .

# Import images into the cluster
k3d image import system-monitor-backend:v1 system-monitor-frontend:v1 -c system-monitor-cluster

# Apply manifests (Secrets, PVCs, Deployments, Services, Ingress, RBAC)
kubectl apply -f k8s/
```

## How to Use the Command Center

1. **Access the Dashboard:** Go to `http://localhost:5173` (Docker) or `http://localhost:8081` (Kubernetes).
2. **Monitor Traffic:** Watch the live telemetry. The system autoscales Nginx replicas when network traffic spikes at 2 MB/s.
3. **Command the AI:** Toggle the top-right switch to `Manual Mode`, open the Chatbot, and type: "Scale up the web server please."

## Simulating Network Load

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