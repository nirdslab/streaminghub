FROM python:3-slim
LABEL maintainer="Yasith Jayawardana <yasith@cs.odu.edu>"

WORKDIR /conduit

# install dependencies
RUN pip3 install numpy pandas pylsl websockets pillow matplotlib lxml jsonschema

# set up project
ENV PYTHONPATH=/conduit
EXPOSE 8765
COPY . .
CMD ["sh", "-c", "LSLAPICFG=/conduit/lsl_api.cfg python3 tools/simulator.py adhd-sin 003ADHD_AV_01.csv & python3 tools/lsl_ws_proxy.py"]
