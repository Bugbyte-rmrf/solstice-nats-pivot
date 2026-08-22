# Blocker Journal

## Entry 1

### Goal
Connect Python to NATS and start the NATS server.

### Problem
Docker would not run properly in my WSL environment, causing "Cannot connect to the Docker daemon" errors, and Docker Desktop failed due to virtualization issues.

### Investigation
I checked if the Docker daemon was running. I tried starting it manually with `sudo service docker start` and `sudo dockerd &`. I also investigated WSL networking limitations (`iptables-legacy`).

### Finding
My environment could not easily support Docker natively via the command line, and dealing with WSL networking configurations was blocking progress on the actual NATS assignment.

### Fix
I bypassed Docker entirely and downloaded the raw NATS server executable directly to my Ubuntu environment using `wget`. I then ran the server natively with the JetStream (`-js`) and monitoring (`-m 8222`) flags.

### Result
The experiment worked. The NATS server started successfully natively, and my Python scripts were able to connect to JetStream.

### Time Spent
45 minutes
