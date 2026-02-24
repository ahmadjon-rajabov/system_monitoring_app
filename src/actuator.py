import docker
import os
import subprocess
from kubernetes import client, config

class Actuator:
    def __init__(self):
        # Where app lives. Options: "docker", "kubernetes" or "safe_mode"
        self.mode = os.getenv("ORCHESTRATOR", "safe_mode").lower()

        self.docker_service_name = "nginx_server"
        self.k8s_deployment_name = "client-deployment"
        self.k8_namespace = "default"

        if self.mode == "docker":
            self._init_docker()
        elif self.mode == "kubernetes":
            self._init_kubernetes()
        else:
            print(f"Unknown orchestrator: {self.mode}. Running in SAFE MODE (No scaling).")
            self.mode = "safe_mode"
    
    def _init_docker(self):
        self.client = None
        try:
            self.client = docker.from_env()
            self.client.ping()  
            return "Connected to standard Docker socket!"
        except Exception as e:
            pass

        if not self.client:
            try:
                print("Standard Docker path failed. Trying macOS user socker...")
                home = os.path.expanduser("~")
                mac_socket = f"unix://{home}/.docker/run/docker.sock"
                self.client = docker.DockerClient(base_url = mac_socket)
                self.client.ping()
                return "Connected to macOS Docker socket!"
            except Exception as e:
                print(f"Could not connect to Docker! Error: {e}")
                self.mode = "safe_mode"
    
    def _init_kubernetes(self):
        try:
            config.load_incluster_config() # loads secure token injected automatically by k8s into the pod
            self.k8s_apps_api = client.AppsV1Api()
            print("Conntected to Kubernetes Control Plane!")
        except:
            try:
                config.load_kube_config()
                print("Loaded local Kubernetes config.")
            except Exception as e:
                print(f"Could not load Kubernetes config: {e}")
                self.mode = "safe_mode"
    
    def get_container_count(self):
        """
        Counts how many nginx_server containers are running
        Returns a dummy value if in k8s mode
        """
        if self.mode == "docker" and self.client:
            return sum(1 for container in self.client.containers.list() if self.docker_service_name in container.name)
        elif self.mode == "kubernetes":
            try:
                # Read client-deployment file and tell me the replicas count
                deployment = self.k8s_apps_api.read_namespaced_deployment(self.k8s_deployment_name, self.k8_namespace)
                return deployment.status.replicas 
            except Exception as e:
                print(f"K8s read error: {e}")
                return 0
        return 0

    def execute_scale(self, target_count):
        if self.mode == "docker":
            subprocess.run(["docker", "compose", "up", "-d", "--scale", f"{self.docker_service_name}={target_count}"])
        elif self.mode == "kubernetes":
            try:
                body = {"spec": {"replicas": target_count}}
                self.k8s_apps_api.patch_namespaced_deployment(
                    name=self.k8s_deployment_name,
                    namespace=self.k8_namespace,
                    body=body
                )
                print(f"Kubernetes Scaling Command Sent. Target: {target_count}", flush=True)
            except Exception as e:
                print(f"K8s scaling failed: {e}", flush=True)
                return 0
        return 0
    
    def scale_up(self):
        """
        Starts a new container
        """
        current = self.get_container_count()
        new_count = current + 1
        self.execute_scale(new_count)
        print(f"Scaling UP to {new_count}")

    def scale_down(self):
        """
        Removes a container 
        """
        current = self.get_container_count()
        if current > 1:
            new_count = current - 1
            self.execute_scale(new_count)
            print(f"Scaling DOWN to {new_count}")
        else:
            print("Cannot scale DOWN below 1")\

if __name__ == "__main__":
    # Test mode
    actuator = Actuator()
    print(f"Current Containers: {actuator.get_container_count()}")