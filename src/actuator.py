import docker
import time, os
import subprocess

class Actuator:
    def __init__(self):
        self.service_name = "nginx_server"
        self.client = None

        try:
            self.client = docker.from_env()
            self.client.ping()
        except Exception:
            pass

        if not self.client:
            try:
                print("Standard Docker path failed. Trying macOS user socker...")
                home = os.path.expanduser("~")
                mac_socket = f"unix://{home}/.docker/run/docker.sock"
                self.client = docker.DockerClient(base_url = mac_socket)
                self.client.ping()
            except Exception as e:
                print(f"Could not connect to Docker! Error: {e}")
                print("Is Docker running")
                raise e
    
    def get_container_count(self):
        """
        Counts how many nginx_server containers are running
        """
        containers = self.client.containers.list()
        count = 0
        for container in containers:
            # Check if container belongs to our project
            if self.service_name in container.name:
                count += 1
        return count
    
    def scale_up(self):
        """
        Starts a new container
        """
        current = self.get_container_count()
        print(f"Scaling UP! (Current: {current})")

        subprocess.run(["docker", "compose", "up", "-d", "--scale", f"nginx_server={current + 1}"])
        print(f"Scaled to {current + 1} replicas")

    def scale_down(self):
        """
        Removes a container 
        """
        current = self.get_container_count()
        if current > 1:
            print(f"Scaling DOWN! (Current: {current})")
            subprocess.run(["docker", "compose", "up", "-d", "--scale", f"nginx_server={current - 1}"])
            print(f"Scaled to {current - 1}")
        else:
            print("Cannot scale DOWN below 1")

if __name__ == "__main__":
    # Test mode
    actuator = Actuator()
    print(f"Current Containers: {actuator.get_container_count()}")