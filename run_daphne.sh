#!/bin/bash
cd /home/ubuntu/spotify_chat_backend_nonsptyWEBapi
source venv/bin/activate
daphne -b 0.0.0.0 -p 8001 backend.asgi:application 