FROM python:3-slim
LABEL maintainer="Yasith Jayawardana <yasith@cs.odu.edu>"

WORKDIR /conduit

# install dependencies
RUN pip3 install jsonschema lxml matplotlib numpy pandas pillow pylsl websockets

# set up project
ENV PYTHONPATH=/conduit
ENV DATASET_DIR=${PYTHONPATH}/datasets
EXPOSE 5000
COPY . .
CMD ["sh", "-c", "python3 tools/simulator.py adhd-sin 003ADHD_AV_01.csv & python3 tools/lsl_ws_proxy.py"]
