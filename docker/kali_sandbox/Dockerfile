FROM kalilinux/kali-rolling:latest

# Set environment
ENV DEBIAN_FRONTEND=noninteractive \
    PIP_BREAK_SYSTEM_PACKAGES=1 \
    PIP_REQUIRE_VIRTUALENV=false

# Update and install tools (using kali-linux-headless which contains all CLI pentesting tools without the heavy GUI/X11 dependencies)
RUN apt-get update && apt-get install -y --no-install-recommends \
    kali-linux-headless \
    python3 \
    python3-pip \
    python3-requests \
    curl \
    nmap \
    bubblewrap \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create workspace root for per-target isolation
RUN mkdir -p /scripthub /workspace && chmod 755 /workspace

# 輕量存活訊號：驗證 /workspace 與 /scripthub 存在（bwrap 隔離功能驗證屬下一輪）
HEALTHCHECK --interval=60s --timeout=10s --retries=3 --start-period=15s \
  CMD test -d /workspace && test -d /scripthub || exit 1

# Keep container alive continuously
CMD ["tail", "-f", "/dev/null"]
