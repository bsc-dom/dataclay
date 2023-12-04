



```bash
docker run \
-v ./config/otel-collector.yaml:/etc/otel-collector.yaml \
otel/opentelemetry-collector-contrib \
"--config=/etc/otel-collector.yaml"


```
