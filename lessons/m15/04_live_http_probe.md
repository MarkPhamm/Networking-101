# Exercise: Probe a live endpoint with `curl`

You've written an HTTP client by hand. Now learn the invocation most
engineers reach for when something's broken: `curl` with the right
flags to extract just the status code.

## The command

```bash
curl -s -o /dev/null -w "%{http_code}" https://example.com > /tmp/http_probe.txt
```

- `-s` — silent; don't show the progress meter.
- `-o /dev/null` — throw the body away; you only care about the status.
- `-w "%{http_code}"` — write the status code (just the digits) to
  stdout.
- `> /tmp/http_probe.txt` — capture that into a file the verifier can
  read.

If the request succeeds, `/tmp/http_probe.txt` will contain the three
digits `200`.

## What to do

Run that command **in your terminal**, then press `v` in `net-learn`.
The verifier checks:

1. `/tmp/http_probe.txt` exists.
2. It contains a 2xx or 3xx status code (`^[23]\d\d$`).

## When you'd use this for real

- CI health checks — bail the pipeline if `/healthz` isn't 200.
- Monitoring — the simplest probe for a blackbox exporter.
- Debugging — "does the origin even return 200 outside the CDN?"
- Load balancer troubleshooting — compare status code between the VIP
  and a backend directly.

## Other `curl` invocations worth memorizing

```bash
# Full request + response on the wire (--verbose)
curl -v https://example.com

# Headers only (HEAD)
curl -I https://example.com

# Follow redirects
curl -L https://bit.ly/anything

# POST JSON
curl -X POST -H "Content-Type: application/json" \
     -d '{"foo":"bar"}' https://api.example.com/things

# Fail on 4xx/5xx (non-zero exit — scriptable)
curl --fail https://api.example.com/thing
```

## DE analogy

Same pattern you use when checking whether a REST API is up before
firing off an Airflow DAG, or confirming a Spark cluster's web UI is
reachable after a deploy. `curl` is the *lingua franca* of "is this
HTTP thing alive?".
