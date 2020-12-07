FROM python:3-slim
LABEL maintainer="Yasith Jayawardana <yasith@cs.odu.edu>"

WORKDIR /conduit

# install dependencies
RUN pip3 install jsonschema lxml matplotlib numpy pandas pillow pylsl websockets

# set up project
ARG WS_PORT=5000
ENV PYTHONPATH=/conduit
ENV DATASET_DIR=${PYTHONPATH}/datasets
EXPOSE ${WS_PORT}
COPY . .
CMD ["sh", "-c", "python3 tools/simulator.py adhd-sin 003ADHD_AV_01.csv & python3 tools/lsl_ws_proxy.py"]

HEALTHCHECK CMD curl -i -N -H "Connection: Upgrade" -H "Upgrade: websocket" -H "Host: localhost" -H "Origin: localhost" localhost:${WS_PORT}