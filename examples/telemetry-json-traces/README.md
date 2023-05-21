



```bash
docker run \
-v ./otel-json-to-jaeger.yaml:/etc/otel-collector.yaml \
otel/opentelemetry-collector-contrib \
"--config=/etc/otel-collector.yaml"


```
