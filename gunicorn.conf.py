# gunicorn.conf.py

bind = "0.0.0.0:$PORT"
# Usar worker síncrono; SocketIO va en modo threading/long-polling
worker_class = "sync"
workers = 1
timeout = 120
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = False
