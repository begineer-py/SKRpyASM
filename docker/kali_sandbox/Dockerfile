FROM kalilinux/kali-rolling:latest

# Set environment
ENV DEBIAN_FRONTEND=noninteractive

# Update and install tools (using kali-linux-headless which contains all CLI pentesting tools without the heavy GUI/X11 dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    kali-linux-headless \
    python3 \
    python3-pip \
    python3-requests \
    curl \
    nmap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create working directory and scripthub
WORKDIR /root
RUN mkdir -p /scripthub

# Keep container alive continuously
CMD ["tail", "-f", "/dev/null"]
