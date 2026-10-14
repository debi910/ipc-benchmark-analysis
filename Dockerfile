FROM ubuntu:24.04

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential python3 python3-venv python3-pip ca-certificates \
    libcap2-bin && rm -rf /var/lib/apt/lists/*

WORKDIR /work
COPY requirements.txt .
RUN python3 -m venv /opt/ipcbench-venv && \
    /opt/ipcbench-venv/bin/pip install --no-cache-dir -r requirements.txt

ENV PATH="/opt/ipcbench-venv/bin:${PATH}"
COPY . .
RUN make all
CMD ["make", "bench-quick"]
