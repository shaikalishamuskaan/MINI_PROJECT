# Media Review System

A CLI-based media review and recommendation system built using Python, SQLAlchemy, and SQLite.

## Features

- User management
- Movie, web show, and song management
- Search media by title
- Submit ratings and reviews
- View reviews
- Top-rated media
- Favorite media
- Bulk review import using CSV
- Personalized recommendations
- Bayesian weighted recommendation algorithm
- Genre-based user preferences
- Async database operations
- Logging
- Unit testing

## Technology Stack

- Python
- SQLAlchemy 2.x
- aiosqlite
- SQLite
- argparse
- pytest
- pytest-asyncio
- Python logging

## Architecture

```text
CLI
 ↓
Service Layer
 ↓
Repository Layer
 ↓
SQLAlchemy
 ↓
SQLite
```

The CLI handles user input and display, the Service Layer contains business logic and validation, and the Repository Layer handles database access.

## Recommendation System

The V1 recommendation engine uses a Bayesian weighted rating:

```text
Weighted Rating =
(v / (v + m)) × R
+
(m / (v + m)) × C
```

Where:

- R = average rating of the media
- v = number of ratings
- C = overall average rating
- m = minimum rating threshold

User genre preferences are also used to personalize the recommendation score. Already-reviewed media are excluded from recommendations.

## Bulk Reviews

Reviews can be imported using a CSV file.

CSV format:

```text
media_id,rating,comment
1,5,Amazing movie
2,4,Really good
3,5,Loved it
```

Example:

```bash
python media_review.py --bulk-review reviews.csv --user-id 1
```

Invalid or duplicate reviews do not stop the entire bulk operation.

## Testing

Run all tests using:

```bash
python -m pytest
```

Tests use an in-memory SQLite database so they do not modify the application's real database.

## Logging

Application logs are stored in:

```text
logs/media_review.log
```

Logs cover:

- Application startup
- Successful reviews
- Validation failures
- Bulk review processing
- Unexpected errors

Passwords and sensitive information are not logged.

## Running the Application

Activate the virtual environment and run:

```bash
python media_review.py --help
```

Example commands:

```bash
python media_review.py --list

python media_review.py --search "Inception"

python media_review.py --top-rated

python media_review.py --reviews 1

python media_review.py --recommend 1
```

Submit a review:

```bash
python media_review.py --review <media_id> <rating> "<comment>" --user-id <user_id>
```

Bulk reviews:

```bash
python media_review.py --bulk-review reviews.csv --user-id <user_id>
```

## Project Structure

```text
MINI_PROJECT/
│
├── app/
│   ├── __init__.py
│   ├── bulk.py
│   ├── db.py
│   ├── logging_config.py
│   ├── models.py
│   ├── recommendation.py
│   ├── repo.py
│   └── services.py
│
├── test/
│   ├── test_bulk.py
│   ├── test_recommendation.py
│   ├── test_repo.py
│   └── test_services.py
│
├── data/
│   ├── media_review.db
│   └── reviews.csv
│
├── logs/
│   └── media_review.log
│
├── media_review.py
├── DESIGN DOC.md
├── requirements.txt
├── pytest.ini
└── README.md
```

## Version 1

V1 provides a clean working MVP with:

- Layered architecture
- Async database access
- Core media review functionality
- Personalized recommendations
- Bulk review processing
- Logging
- Unit tests

## Version 2

V2 will enhance the existing architecture with:

- Factory Pattern
- Advanced recommendation techniques
- Redis caching
- Observer Pattern
- Multithreaded bulk processing
- Textual terminal UI
- Improved authentication and session management
