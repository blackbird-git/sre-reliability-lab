
# Image vs Container

An image is a static read-only package containing everything needed to run an application. 
Images are immutable and cannot be changed once built. 
Stacked filesystem layers; OS--packages--code

A container is a dynamic, isolated execution environment. 
The Docker engine adds a temporary read-write layer (mutable) on top of the image. 
A container contains everything needed to run a specific application. 

# Host port vs Container Port

Accessing any port locally from the host will only route to the local machine.
We mapped local port 8080 to container port 80 to access the container through localhost.

# Stop/Start vs Remove/Recreate

A docker container may be stopped and started and any changes made will persist. When a docker container is removed and recreated, it is recreated from the source image. Any changes written to the container's filesystem do not persist. A way around this is to mount storage to the container where any file changes are written. These file changes persist with container removal.

A container's writeable layer lives on disk when the container is stopped. This is how it survives stops/starts.

# Container Storage vs bind mount
See above. Bind mount is a way to mount a host directory (for example) to a directory on the container. By default this makes the host directory accessible and writeable.

# Why use Read-Only
A read-only bind mount lets Nginx serve the host files while preventing processes inside the container from modifying them. It limits write access if the application is compromised.

# docker run -d --name lab-web -p 127.0.0.1:8080:80 --mount type=bind,src=/home/ilyam/projects/sre-reliability-lab/web,dst=/usr/share/nginx/html,ro nginx:stable 