# Media Review System

A CLI-based media review and recommendation system built using Python, SQLAlchemy, SQLite, Redis, and Textual.

The system allows users to manage media, submit reviews and ratings, favorite media, receive personalized recommendations, and receive notifications when reviews are added to favorited media.

The project is developed in two versions:

- V1 - Basic working MVP
- V2 - Enhanced version with design patterns, caching, authentication, multithreading, and Textual UI

---

## Features

### Core Features

- User management
- User authentication
- Session management
- Movie, web show, and song management
- Search media by title
- Submit ratings and reviews
- View reviews
- Top-rated media
- Favorite media
- View notifications
- Bulk review import using CSV
- Personalized recommendations

### V2 Features

- Factory Pattern for media creation
- Redis caching for frequently accessed reviews
- Cache invalidation after new reviews
- Observer Pattern for notifications
- Multithreaded bulk review processing
- Textual terminal UI
- Password hashing using bcrypt
- Enhanced recommendation scoring
- Application logging
- Unit testing

---

## Technology Stack

- Python
- SQLAlchemy 2.x
- aiosqlite
- SQLite
- Redis
- Memurai (Windows Redis-compatible server)
- argparse
- Textual
- bcrypt
- pytest
- pytest-asyncio
- Python logging
- ThreadPoolExecutor
- Git

---

## Architecture

The application follows a layered architecture:

```text
                 CLI / Textual UI
                        |
                        v
                 Service Layer
                        |
                        v
                Repository Layer
                        |
                        v
                   SQLAlchemy
                        |
                        v
                     SQLite
```

V2 adds supporting components:

```text
CLI / Textual UI
       |
       v
Service Layer
   |    |    |    |
   |    |    |    +--> Recommendation Engine
   |    |    +-------> Observer
   |    +------------> Redis Cache
   +-----------------> Repository
                          |
                          v
                       SQLite
```

### Responsibilities

**UI Layer**

Handles user interaction through the Textual terminal interface. The original argparse CLI is also retained for command-line operations.

**Service Layer**

Contains business logic, validation, authentication, recommendation coordination, and review processing.

**Repository Layer**

Handles database operations using SQLAlchemy.

**Cache Layer**

Uses Redis with a cache-aside strategy for frequently accessed reviews.

**Observer Layer**

Creates notifications when a new review is submitted for favorited media.

**Recommendation Engine**

Calculates personalized recommendations using weighted/Bayesian rating scores together with user preference information.

---

## Database

The application uses SQLite with SQLAlchemy's asynchronous ORM.

Main entities:

```text
USERS
MEDIA
REVIEWS
FAVORITES
NOTIFICATIONS
```

Relationships include:

- Users can write multiple reviews.
- Media can receive multiple reviews.
- Users can favorite multiple media items.
- Media can be favorited by multiple users.
- Users can receive multiple notifications.
- A user can have only one review for a particular media item.

The `reviews` table enforces a unique combination of:

```text
user_id + media_id
```

---

## Authentication and Sessions

V2 provides basic user authentication.

Passwords are never stored as plain text.

Passwords are hashed using `bcrypt` when a user is created.

During login:

```text
Username + Password
        |
        v
Find user
        |
        v
Verify bcrypt password
        |
        v
Create application session
```

The session stores the currently authenticated user's ID and username for the running application process.

Each terminal/application process maintains its own in-memory session.

---

## Recommendation System

The recommendation engine uses a Bayesian weighted rating approach.

```text
Weighted Rating =
(v / (v + m)) × R
+
(m / (v + m)) × C
```

Where:

- `R` = average rating of the media
- `v` = number of ratings
- `C` = overall average rating
- `m` = minimum rating threshold

The recommendation score is further enhanced using user preference signals such as:

- Genre preferences
- Media-type preferences

Already-reviewed media is excluded from recommendations.

This approach prevents media with very few ratings from automatically appearing above consistently well-rated media.

---

## Redis Caching

V2 uses Redis to cache frequently accessed reviews.

The cache follows the **Cache-Aside** pattern.

Example cache key:

```text
media_reviews:<media_id>
```

Example:

```text
media_reviews:2
```

### Cache flow

```text
Request reviews
      |
      v
Check Redis
   /      \
 HIT      MISS
  |         |
  v         v
Return    SQLite
cached      |
data        v
          Store in Redis
              |
              v
          Return reviews
```

Cached reviews have a TTL of 300 seconds.

When a new review is created, the corresponding media review cache is invalidated.

---

## Observer Pattern

V2 uses an in-process Python Observer Pattern.

Redis Pub/Sub is not used for notifications.

When a review is created:

```text
New Review
    |
    v
ReviewService
    |
    v
NotificationObserver
    |
    v
Find users who favorited the media
    |
    v
Create notifications
```

The reviewer themselves is not notified.

Notifications are stored in the `notifications` database table and can be viewed through the Textual interface.

---

## Multithreaded Bulk Reviews

Reviews can be imported from a CSV file.

CSV format:

```text
media_id,rating,comment
1,5,Amazing movie
2,4,Really good
3,5,Loved it
```

V2 processes multiple rows using `ThreadPoolExecutor`.

Each worker creates its own SQLAlchemy `AsyncSession` instead of sharing a session between threads.

This is important because an `AsyncSession` should not be shared across concurrent operations.

The bulk processor reports:

```text
Successful: X
Failed: Y
```

A failed review does not stop the processing of other valid rows.

Bulk processing also integrates with:

- Redis cache invalidation
- Observer notifications
- Review validation
- Logging

---

## Textual Terminal UI

V2 provides a complete terminal-based user interface using Textual.

The UI supports:

- Login
- Logout
- Create User
- Add Media
- List Media
- Search Media
- Top Rated
- Add Review
- View Reviews
- Add Favorite
- View Favorites
- Recommendations
- Notifications
- Bulk Review CSV import

Run the Textual application using:

```bash
python -m app.ui
```

---

## Logging

Application logs are stored in:

```text
logs/media_review.log
```

Logging covers important application events such as:

- Application startup
- Review creation
- Cache hits and misses
- Cache invalidation
- Bulk review processing
- Validation failures
- Database constraint failures
- Recommendation generation
- Notification creation

Passwords and sensitive information are not logged.

---

## Testing

Run all tests using:

```bash
python -m pytest
```

Tests use an in-memory SQLite database where appropriate so that tests do not modify the application's real database.

The test suite covers areas including:

- Repository operations
- Service validation
- Recommendations
- Bulk review processing
- Authentication
- Sessions
- V2 functionality

---

## Running the Application

### 1. Activate the virtual environment

Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run the Textual UI

```powershell
python -m app.ui
```

### 3. Run the original CLI

Display available commands:

```powershell
python media_review.py --help
```

Example commands:

```powershell
python media_review.py --list
python media_review.py --search "Inception"
python media_review.py --top-rated
python media_review.py --reviews 1
python media_review.py --recommend 1
```

Submit a review:

```powershell
python media_review.py --review <media_id> <rating> "<comment>" --user-id <user_id>
```

Bulk reviews:

```powershell
python media_review.py --bulk-review reviews.csv --user-id <user_id>
```

---

## Project Structure

```text
MINI_PROJECT/
│
├── app/
│   ├── __init__.py
│   ├── bulk.py
│   ├── cache.py
│   ├── db.py
│   ├── logging_config.py
│   ├── models.py
│   ├── recommendation.py
│   ├── repo.py
│   ├── services.py
│   ├── auth.py
│   ├── session.py
│   ├── ui.py
│   │
│   ├── media/
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── movie.py
│   │   ├── web_show.py
│   │   ├── song.py
│   │   └── factory.py
│   │
│   └── observers/
│       ├── __init__.py
│       ├── base.py
│       └── notification.py
│
├── test/
│   ├── conftest.py
│   ├── test_auth.py
│   ├── test_bulk.py
│   ├── test_recommendation.py
│   ├── test_repo.py
│   ├── test_services.py
│   └── test_session.py
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
├── requirments.txt
├── pytest.ini
├── .gitignore
└── README.md
```

---

# Version 1

V1 provides the basic working MVP.

### V1 includes:

- Layered architecture
- Async SQLAlchemy database access
- SQLite database
- User management
- Media management
- Reviews and ratings
- Favorites
- Search
- Top-rated media
- Bulk review processing
- Bayesian weighted recommendations
- Genre-based recommendations
- Logging
- Unit testing

V1 is tagged in Git as:

```text
v1.0
```

---

# Version 2

V2 enhances the V1 architecture without replacing it.

### V2 includes:

- Factory Pattern
- Redis caching
- Cache invalidation
- Observer Pattern
- Notification system
- Multithreaded bulk review processing
- Enhanced recommendation scoring
- bcrypt password hashing
- Authentication
- Application session management
- Complete Textual terminal UI
- Additional tests and integration

V2 maintains the same core database model and layered architecture while adding supporting components for scalability, maintainability, and a better user experience.

---

## Git Development

The project was developed using meaningful Git commits for major features.

Major development stages include:

```text
Initialize project structure
        ↓
Async SQLAlchemy database configuration
        ↓
Database models
        ↓
Repository layer
        ↓
Service layer
        ↓
Review retrieval and top-rated media
        ↓
V1 completion
        ↓
Media Factory Pattern
        ↓
Redis caching
        ↓
Enhanced recommendations
        ↓
Observer notifications
        ↓
Multithreaded bulk processing
        ↓
Textual UI
        ↓
Authentication and sessions
        ↓
Final V2 integration
```

---

## Version

Current project version:

```text
V2.0
```

V1 milestone:

```text
v1.0
```

V2 milestone:

```text
v2.0
```
