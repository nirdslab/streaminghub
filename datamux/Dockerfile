FROM python:3-slim
LABEL maintainer="Yasith Jayawardana <yasith@cs.odu.edu>"

WORKDIR /conduit

# install dependencies
RUN pip3 install jsonschema lxml matplotlib numpy pandas pillow pylsl websockets

# set up project
ARG PORT=5000
ENV PORT=${PORT}
ENV PYTHONPATH=/conduit
ENV SHUB_DATA_DIR=${PYTHONPATH}/datasets
ENV SHUB_META_DIR=${PYTHONPATH}/repository
EXPOSE ${PORT}
COPY . .
CMD ["sh", "-c", "python3 tools/simulator.py adhd-sin 003ADHD_AV_01.csv & python3 tools/lsl_ws_proxy.py"]