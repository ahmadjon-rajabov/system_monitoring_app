import docker
import time 
import subprocess

class Actuator:
    def __init__(self):
        self.client = docker.from_env() # connect to local docker daemon
        self.service_name = "nginx_server"
    
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

    # Test scale UP
    actuator.scale_up()
    time.sleep(5)
    print(f"New Count: {actuator.get_container_count()}")

    #Test scale down
    actuator.scale_down()