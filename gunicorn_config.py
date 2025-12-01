import os

# Gunicorn configuration file

# Bind to the port provided by the environment (Render, etc.)
bind = f"0.0.0.0:{os.getenv('PORT', '10000')}"

# Use a single synchronous worker; the app uses standard threads
workers = int(os.getenv("WEB_CONCURRENCY", "1"))
worker_class = "sync"

# Reasonable timeouts for slow DB / email operations
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = 2

