# Price Tracker API

A lightweight REST API built with FastAPI that monitors product prices on any webpage and alerts you when prices drop to your target.

## Features

- Track products by URL with a personal target price
- Automatic background price checking every minute
- Console alerts when prices drop to or below your target
- User management with automatic account creation
- SQLite database (swap to PostgreSQL by changing one line)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Framework | FastAPI |
| ORM | SQLAlchemy 2.0 |
| Database | SQLite (PostgreSQL-ready) |
| HTTP Client | httpx |
| HTML Parser | BeautifulSoup4 |
| Scheduler | APScheduler |
| Validation | Pydantic v2 |

## Project Structure

```
Price-Tracker-API/
├── main.py          # FastAPI app, endpoints, scheduler
├── models.py        # SQLAlchemy User & TrackedProduct models
├── database.py      # DB engine, session, dependency injection
├── scraper.py       # Async web scraper for price extraction
└── tracker.db       # SQLite database (auto-created)
```

## Quick Start

### 1. Install dependencies

```bash
pip install fastapi uvicorn sqlalchemy httpx beautifulsoup4 apscheduler
```

### 2. Run the server

```bash
uvicorn main:app --reload
```

The API starts at `http://localhost:8000`. Interactive docs at `http://localhost:8000/docs`.

## API Endpoints

### `POST /track`

Track a new product.

**Request:**
```json
{
  "url": "https://example.com/product/123",
  "user_email": "you@email.com",
  "target_price": 49.99
}
```

**Response:**
```json
{
  "status": "success",
  "data": {
    "product_id": "a1b2c3d4-..."
  },
  "message": "Product tracked successfully"
}
```

### `GET /products/{user_email}`

Get all products tracked by a user.

**Response:**
```json
{
  "status": "success",
  "data": [
    {
      "id": "a1b2c3d4-...",
      "url": "https://example.com/product/123",
      "target_price": 49.99,
      "current_price": 44.99,
      "last_checked": "2026-06-28T12:00:00Z"
    }
  ],
  "message": "Products retrieved successfully"
}
```

## How It Works

1. **Track** a product via `POST /track` with a URL and target price
2. The **scraper** immediately fetches the current price using `httpx` + `BeautifulSoup`
3. A **background scheduler** re-checks all tracked products every 60 seconds
4. If `current_price <= target_price`, a **console alert** fires:
   ```
   🚨 ALERT: Price dropped for https://example.com/product to 39.99!
   ```

## Database Schema

### User
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| email | VARCHAR(255) | Unique, Indexed |
| created_at | TIMESTAMP | Server Default |

### TrackedProduct
| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | Primary Key |
| user_id | UUID | FK -> User (CASCADE) |
| url | TEXT | Not Null |
| target_price | FLOAT | Not Null |
| current_price | FLOAT | Nullable |
| last_checked | TIMESTAMP | Nullable |

## Switching to PostgreSQL

In `database.py`, replace the `DATABASE_URL`:

```python
# SQLite (default)
DATABASE_URL = "sqlite:///./tracker.db"

# PostgreSQL
DATABASE_URL = "postgresql+asyncpg://user:password@localhost:5432/price_tracker"
```

Then install the async driver:

```bash
pip install asyncpg
```

## License

MIT
