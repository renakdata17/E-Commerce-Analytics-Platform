Apache Flink streaming jobs package this directory for real-time KPIs (e.g. rolling windows on order revenue).

Suggested layout:

- Java or Python Flink API jobs with explicit state TTL and keyed streams.
- Separate job-specific configuration (parallelism, checkpoint interval) injected at deploy time.
