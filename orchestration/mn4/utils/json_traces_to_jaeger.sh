#!/bin/bash

# Script to visualize the mn4 json traces in jaeger

# Stop jaeger container
docker stop jaeger
docker rm jaeger

# Start Jaeger
docker run -d --name jaeger \
  -e COLLECTOR_ZIPKIN_HOST_PORT=:9411 \
  -p 5775:5775/udp \
  -p 6831:6831/udp \
  -p 6832:6832/udp \
  -p 5778:5778 \
  -p 16686:16686 \
  -p 14268:14268 \
  -p 14250:14250 \
  -p 9411:9411 \
  jaegertracing/all-in-one:latest

# Copy json traces from MareNostrum
BSC_USER=bsc25877
scp $BSC_USER@mn1.bsc.es:~/.dataclay/otel-traces.json .

# Start OpenTelemetry Colector to read json and sent it to Jaeger
timeout 30 bin/otelcontribcol_linux_amd64 --config config/otel-json-to-jaeger.yaml &

# Open Jaeger in http://localhost:16686/search