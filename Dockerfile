ARG DATACLAY_PYVER
FROM python:$DATACLAY_PYVER
LABEL maintainer dataClay team <support-dataclay@bsc.es>
# LC_CTYPE instanciated for singularity
ENV LC_CTYPE=en_US.UTF-8

# Create workdir
RUN mkdir -p /usr/src/dataclay/deploy/source
WORKDIR /usr/src/dataclay

# Install dataClay dependencies
COPY requirements.txt requirements.txt
#RUN pip install --no-binary :all: -r requirements.txt
RUN pip install -r requirements.txt

# Install dataClay
RUN mkdir src
COPY ./src/dataclay src/dataclay
COPY ./src/storage src/storage
COPY ./setup.py setup.py
RUN python setup.py -q install
RUN rm -rf src
# Execute
# Don't use CMD in order to keep compatibility with singularity container's generator
ENTRYPOINT python -m dataclay.executionenv.server
