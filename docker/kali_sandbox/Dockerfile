# Pinned Kali base image for reproducibility (2024.2 release)
FROM kalilinux/kali-rolling:2024.2

# Set environment
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_REQUIRE_VIRTUALENV=false

# Install only essential pentesting tools (not full kali-linux-headless)
# This reduces attack surface significantly (~2GB vs ~500MB)
RUN apt-get update && apt-get install -y --no-install-recommends \
    nmap \
    ncat \
    netcat-traditional \
    dnsutils \
    iputils-ping \
    curl \
    wget \
    python3 \
    python3-pip \
    python3-requests \
    bubblewrap \
    ca-certificates \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create workspace root for per-target isolation
RUN mkdir -p /scripthub /workspace && chmod 755 /workspace

# Create non-root user for sandbox operations
RUN groupadd -r sandbox && useradd -r -g sandbox -d /workspace -s /bin/bash sandbox \
    && chown -R sandbox:sandbox /workspace /scripthub

# 輕量存活訊號：驗證 /workspace 與 /scripthub 存在（bwrap 隔離功能驗證屬下一輪）
HEALTHCHECK --interval=60s --timeout=10s --retries=3 --start-period=15s \
  CMD test -d /workspace && test -d /scripthub || exit 1

# Switch to non-root user
USER sandbox

# Keep container alive continuously
CMD ["tail", "-f", "/dev/null"]
