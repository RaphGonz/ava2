# Ava Backend Makefile
# All targets must be run from the backend/ directory:
#   cd backend && make dev
#
# Or from project root:
#   make -C backend dev

.PHONY: dev prod install ngrok

## Install Python dependencies
install:
	pip install -r requirements.txt

## Start development server with hot reload on port 8000
dev:
	uvicorn app.main:app --reload --port 8000

## Start production server (4 workers, UvicornWorker)
prod:
	gunicorn -w 4 -k uvicorn.workers.UvicornWorker app.main:app

## Start ngrok tunnel to expose port 8000 for WhatsApp webhook development
## Requires ngrok installed: https://ngrok.com/download
ngrok:
	ngrok http 8000
