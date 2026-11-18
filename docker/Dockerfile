# Dockerfile for Cooja WSN Environmental Monitoring Simulation
FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV CONTIKI=/home/user/contiki-ng

# Install system dependencies, Java runtime, Ant, GCC, and MSP430 toolchain
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc-msp430 \
    msp430-libc \
    default-jdk \
    ant \
    python3 \
    python3-pip \
    git \
    make \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Create working user
RUN useradd -ms /bin/bash user
USER user
WORKDIR /home/user

# Clone Contiki-NG with submodules
RUN git clone --recursive -b develop https://github.com/contiki-ng/contiki-ng.git /home/user/contiki-ng

# Pre-build Cooja
WORKDIR /home/user/contiki-ng/tools/cooja
RUN ant jar

# Set workspace directory
WORKDIR /home/user/project

# Default command: run simulation headless
CMD ["bash", "cooja-simulations/scripts/run_simulation_headless.sh"]
