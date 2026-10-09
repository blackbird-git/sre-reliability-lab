
# Image vs Container

An image is a static read-only file containing everything needed to run an application. 
Images are immutable and cannot be changed once built. 
Stacked filesystem layers; OS--packages--code
Images are stored on disk.

A container is a dynamic, isolated execution environment. 
The Docker engine adds a temporary read-write layer (mutable) on top of the image. 
A container contains everything needed to run a specific application. 
Containers are stored in RAM.

# Host port vs Container Port

Accessing any port locally from the host will only route to the local machine.
Container ports must be mapped to local ports in order to pass traffic through from the host to the container.

# Stop/Start vs Remove/Recreate

A docker container may be stopped and started and any changes made will persist. When a docker image is removed and recreated, it is recreated from the source image. Any changes written to the container's filesystem do not persist. A way around this is to mount storage to the container where any file changes are written. These file changes persist with container removal.

# Container Storage vs bind mount
See above. Bind mount is a way to mount a host directory (for example) to a directory on the container. By default this makes the host filesystem accessible and writeable.

# Why use Read-Only
See above. This creates an attack vector by exposing host filesystems. 
