# Chess Ranker

A FastAPI-based web app to explore, visualize, and export chess player ratings from Lichess.org.

## Features
- List top chess players by type (classical, blitz, rapid)
- Visualize rating history for any player or top N players
- Download CSVs of rating histories
- Interactive frontend (HTML/JS/CSS, Plotly.js)
- Redis-backed caching for fast, scalable performance
- Docker and Docker Compose support (includes Redis)

## Quick Start

```sh
docker compose up --build
```

App: http://localhost:8000/

## Requirements
- Docker
- Docker Compose

## Environment
- Python 3.13
- FastAPI, Redis, redis-om, Plotly.js 