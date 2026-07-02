"""Execution lifecycle constants."""

# Age, in seconds, after which a still-RUNNING execution is considered stuck
# (e.g. the worker crashed mid-run) and is reaped to FAILED.
STUCK_EXECUTION_TIMEOUT_SECONDS = 3600
