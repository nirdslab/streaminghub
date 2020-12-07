FROM python:3-slim
LABEL maintainer="Yasith Jayawardana <yasith@cs.odu.edu>"

WORKDIR /conduit

# install dependencies
RUN apt-get -q update && \
apt-get install -qy build-essential curl cmake && \
mkdir /tmp/liblsl && \
curl -L0 https://github.com/sccn/liblsl/archive/v1.14.0.tar.gz | tar --strip 1 -C /tmp/liblsl -zxvf - && \
cmake -S /tmp/liblsl -B /tmp/liblsl/build && \
cmake --build /tmp/liblsl/build -j --config Release --target install && \
rm -rf /tmp/liblsl && \
pip3 install numpy pandas pylsl websockets pillow matplotlib beautifulsoup4

# set up project
COPY tools/ tools/
ENV PYTHONPATH=/conduit
EXPOSE 8765
CMD ["python3", "./tools/lsl_ws_proxy.py"]
