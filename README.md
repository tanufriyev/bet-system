# Betting System

## Overview
A microservices-based betting system that allows users to place bets on events. The system consists of two independent services:
- `line-provider`: Manages events and their statuses
- `bet-maker`: Handles bet placement and tracking

## System Architecture

### line-provider Service
- Provides information about available events
- Manages event statuses (NEW, WIN, LOSE)
- Notifies bet-maker about event status changes
- Stores events in memory
- Exposes REST API for event management

### bet-maker Service
- Places bets on events
- Tracks bet statuses
- Updates bet outcomes based on event results
- Uses PostgreSQL for persistent storage
- Uses Redis for event data caching
- Exposes REST API for bet management

## Project Structure
```
betting-system/
├── docker-compose.yml
├── requirements.txt
├── README.md
├── line-provider/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app.py
│   └── tests/
│       └── test_app.py
└── bet-maker/
    ├── Dockerfile
    ├── requirements.txt
    ├── app.py
    ├── models.py
    ├── schemas.py
    ├── cache.py
    ├── alembic.ini
    ├── scripts/
    │   └── run_migrations.sh
    └── migrations/
        ├── env.py
        └── versions/
            └── 001_initial.py
    
```

## Prerequisites
- Docker and Docker Compose
- Python 3.10 or higher (for local development)
- PostgreSQL (handled by Docker)
- Redis (handled by Docker)

## Installation & Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd bet-system
```

2. Build and start the services:
```bash
docker-compose up --build
```

The services will be available at:
- line-provider: http://localhost:8000
- bet-maker: http://localhost:8001

## API Documentation

### line-provider API

#### Get All Events
```
GET /events
```
Returns list of all available events.

#### Get Specific Event
```
GET /event/{event_id}
```
Returns details of a specific event.

#### Change Event Status
```
POST /change-event-state/{event_id}
Body:
{
  "state": "2" or "3"
}
```

### bet-maker API

#### Get Available Events
```
GET /events
```
Returns list of events available for betting.

#### Place Bet
```
POST /bet
Body:
{
    "event_id": string,
    "amount": float
}
```

#### Get Bet History
```
GET /bets
```
Returns list of all bets with their current statuses.

## Usage Examples

1. Get available events:
```bash
curl http://localhost:8001/events
```

2. Place a bet:
```bash
curl --location 'http://localhost:8001/bet' \
--header 'Content-Type: application/json' \
--data '{
    "event_id": "4",
    "amount": 1000
}'
```

3. Check bet status:
```bash
curl --location 'http://localhost:8001/bets'
```

4. Change event status:
```bash
curl --location 'http://localhost:8000/change-event-state/4' \
--header 'Content-Type: application/json' \
--data '{
    "state": "2"
}'
```

5. Post new event for line-provider:
```bash
curl --location --request PUT 'http://localhost:8000/event' \
--header 'Content-Type: application/json' \
--data '{
    "event_id": "4",
    "coefficient": 1.8,
    "deadline": 1932983614,
    "state": "1"
}'
```

## Development

### Database Migrations
```bash
# Create new migration
docker-compose exec bet-maker alembic revision -m "description"

# Run migrations
docker-compose exec bet-maker alembic upgrade head

# Rollback migration
docker-compose exec bet-maker alembic downgrade -1
```

### Code Style
The project follows PEP 8 guidelines. To check code style:
```bash
pip install flake8
flake8 .
```

## Monitoring & Maintenance

### Cache Statistics
```bash
curl http://localhost:8001/internal/cache-stats
```


## Configuration

Environment variables for bet-maker:
- `DATABASE_URL`: PostgreSQL connection string
- `REDIS_URL`: Redis connection string
- `LINE_PROVIDER_URL`: URL of line-provider service
- `HOST`: Service host (default: 0.0.0.0)
- `PORT`: Service port (default: 8001)

Environment variables for line-provider:
- `HOST`: Service host (default: 0.0.0.0)
- `PORT`: Service port (default: 8000)


### Logs
```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs bet-maker
docker-compose logs line-provider
