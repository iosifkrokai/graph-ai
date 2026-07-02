"""Node execution retry and timeout constants."""

# Maximum number of attempts for a single node (initial try + retries).
MAX_NODE_ATTEMPTS = 3

# Base delay, in seconds, for exponential backoff between node retries.
RETRY_BACKOFF_BASE_SECONDS = 0.5

# Wall-clock time budget, in seconds, for a single node attempt.
NODE_TIMEOUT_SECONDS = 300
