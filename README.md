# Chess Ranker

A FastAPI-based web app to explore, visualize, and export chess player ratings from Lichess.org.

## Screenshots
<img width="1486" alt="Screenshot 2025-07-02 at 22 34 37" src="https://github.com/user-attachments/assets/eb4bda60-df5e-4c64-a04c-c09afbf2ca05" />
<img width="1223" alt="Screenshot 2025-07-02 at 22 34 31" src="https://github.com/user-attachments/assets/306cca6b-36ec-4886-bd39-35233615f88c" />
<img width="1467" alt="Screenshot 2025-07-02 at 22 34 23" src="https://github.com/user-attachments/assets/754f58f8-873e-431a-8560-2c087ee80600" />
<img width="1790" alt="Screenshot 2025-07-02 at 22 34 17" src="https://github.com/user-attachments/assets/7f913225-b2c8-4c96-a0a3-e1da582e8686" />


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
