FROM ubuntu
RUN apt-get update \
  && apt-get install -y \
    netcat \
  && apt-get clean \
  && rm -rf /var/lib/apt/lists/*