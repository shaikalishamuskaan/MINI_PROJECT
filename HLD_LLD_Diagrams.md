# HLD & LLD Diagrams — Media Review System

This document contains only the two final architecture diagrams for the current V2 Media Review System.


---

# 1. High-Level Design (HLD)

```mermaid
flowchart TD

    UI["Textual UI<br/>Main User Interface"]

    AUTH["Authentication & Session<br/>Login / Logout / Current User"]

    SERVICES["Service Layer<br/>UserService<br/>MediaService<br/>ReviewService<br/>FavoriteService"]

    REC["Recommendation Engine<br/>Enhanced Bayesian / Weighted Scoring<br/>Genre + Media-Type Preferences"]

    FACTORY["Media Factory<br/>Movie / Web Show / Song"]

    BULK["Bulk Review Processing<br/>ThreadPoolExecutor"]

    REPO["Repository Layer<br/>User / Media / Review / Favorite / Notification"]

    CACHE["Redis Cache<br/>Cache-Aside<br/>Review Cache + TTL"]

    OBS["Observer Pattern<br/>Review Added Event<br/>Notification Observer"]

    LOG["Logging<br/>Application Diagnostics"]

    DB[("SQLite Database<br/>Users / Media / Reviews<br/>Favorites / Notifications")]

    REDIS[("Redis")]

    TESTS["Pytest Test Suite"]

    UI --> AUTH
    UI --> SERVICES
    UI --> REC
    UI --> BULK

    AUTH --> SERVICES

    BULK --> SERVICES

    SERVICES --> FACTORY
    SERVICES --> REC
    SERVICES --> REPO
    SERVICES --> CACHE
    SERVICES --> OBS
    SERVICES --> LOG

    REC --> REPO

    REPO --> DB

    CACHE --> REDIS
    CACHE -. "Cache miss / invalidation" .-> REPO

    OBS --> REPO
    OBS --> DB

    TESTS -. "Tests application components" .-> SERVICES
    TESTS -.-> REPO
    TESTS -.-> REC
    TESTS -.-> AUTH
    TESTS -.-> BULK

    style UI stroke-width:2px
    style SERVICES stroke-width:2px
    style DB stroke-width:2px
    style REDIS stroke-width:2px
```

### HLD Flow

**Textual UI → Services → Repository → SQLite**

Supporting components:
- **Authentication & Session** manages the currently logged-in user.
- **Media Factory** creates the appropriate media object.
- **Recommendation Engine** generates recommendations using the enhanced in-house scoring algorithm.
- **Redis** caches frequently accessed media reviews.
- **Observer** creates notifications when a review is added.
- **ThreadPoolExecutor** processes multiple bulk reviews concurrently.
- **Logging** records application and diagnostic events.
- **Pytest** validates the application components.

---

# 2. Low-Level Design (LLD)

```mermaid
classDiagram

    class User {
        +int id
        +str username
        +str password_hash
    }

    class Media {
        +int id
        +str title
        +str media_type
        +str genre
        +int release_year
    }

    class Review {
        +int id
        +int user_id
        +int media_id
        +int rating
        +str comment
        +datetime created_at
    }

    class Favorite {
        +int user_id
        +int media_id
    }

    class Notification {
        +int id
        +int user_id
        +int media_id
        +str message
        +int is_read
        +datetime created_at
    }

    class UserRepository {
        +create_user()
        +get_user()
        +get_user_by_username()
    }

    class MediaRepository {
        +create_media()
        +get_media()
        +get_all_media()
        +search_media()
    }

    class ReviewRepository {
        +create_review()
        +get_reviews()
        +get_top_rated()
        +get_rating_statistics()
        +get_global_rating_statistics()
        +get_user_genre_ratings()
        +get_user_reviewed_media_ids()
        +get_user_media_type_ratings()
    }

    class FavoriteRepository {
        +add_favorite()
        +get_favorites()
        +get_users_who_favorited()
    }

    class NotificationRepository {
        +create_notification()
        +get_notifications()
    }

    class UserService {
        +create_user()
    }

    class MediaService {
        +create_media()
        +get_all_media()
        +search_media()
    }

    class ReviewService {
        +create_review()
        +get_reviews()
        +get_top_rated()
        +notify_observers()
    }

    class FavoriteService {
        +add_favorite()
        +get_favorites()
    }

    class AuthService {
        +login()
        -verify_password()
    }

    class Session {
        +int user_id
        +str username
        +bool is_authenticated
        +login()
        +logout()
    }

    class RecommendationEngine {
        +recommend()
        -calculate_score()
    }

    class CacheService {
        +get()
        +set()
        +delete()
        +close()
    }

    class ReviewObserver {
        <<abstract>>
        +update()
    }

    class NotificationObserver {
        +update()
    }

    class MediaFactory {
        <<factory>>
        +create_media()
    }

    class Movie {
        +media_type
    }

    class WebShow {
        +media_type
    }

    class Song {
        +media_type
    }

    class BulkProcessor {
        +process_bulk_reviews()
        +process_single_review()
    }

    class TextualUI {
        +login()
        +create_user()
        +add_media()
        +add_review()
        +view_reviews()
        +favorites()
        +recommendations()
        +notifications()
        +bulk_reviews()
    }

    TextualUI --> AuthService
    TextualUI --> Session
    TextualUI --> UserService
    TextualUI --> MediaService
    TextualUI --> ReviewService
    TextualUI --> FavoriteService
    TextualUI --> RecommendationEngine
    TextualUI --> BulkProcessor

    AuthService --> UserRepository
    AuthService --> Session

    UserService --> UserRepository
    MediaService --> MediaRepository
    MediaService --> MediaFactory

    ReviewService --> ReviewRepository
    ReviewService --> UserRepository
    ReviewService --> MediaRepository
    ReviewService --> CacheService
    ReviewService --> ReviewObserver

    FavoriteService --> FavoriteRepository
    FavoriteService --> UserRepository
    FavoriteService --> MediaRepository

    RecommendationEngine --> ReviewRepository
    RecommendationEngine --> MediaRepository

    NotificationObserver ..|> ReviewObserver
    NotificationObserver --> FavoriteRepository
    NotificationObserver --> NotificationRepository

    BulkProcessor --> ReviewService
    BulkProcessor --> UserRepository
    BulkProcessor --> MediaRepository
    BulkProcessor --> FavoriteRepository
    BulkProcessor --> NotificationRepository
    BulkProcessor --> CacheService
    BulkProcessor --> NotificationObserver

    MediaFactory --> Movie
    MediaFactory --> WebShow
    MediaFactory --> Song

    UserRepository --> User
    MediaRepository --> Media
    ReviewRepository --> Review
    FavoriteRepository --> Favorite
    NotificationRepository --> Notification

    User "1" --> "*" Review
    Media "1" --> "*" Review
    User "1" --> "*" Favorite
    Media "1" --> "*" Favorite
    User "1" --> "*" Notification
    Media "1" --> "*" Notification
```

### LLD Key Points

- **Repository layer** handles database access through SQLAlchemy.
- **Service layer** contains application/business logic.
- **AuthService** verifies bcrypt password hashes.
- **Session** is an in-memory, per-process session for the logged-in user.
- **MediaFactory** creates `Movie`, `WebShow`, or `Song` objects.
- **ReviewService** coordinates review creation, caching, and observer notifications.
- **CacheService** uses Redis with cache-aside behavior and TTL.
- **NotificationObserver** reacts to newly created reviews and creates notification records for users who favorited the media, excluding the reviewer.
- **RecommendationEngine** uses Bayesian/weighted scoring plus genre and media-type preferences and excludes already reviewed media.
- **BulkProcessor** uses `ThreadPoolExecutor` for multiple CSV review rows, with a separate async database session per worker.
- **TextualUI** is the complete user-facing interface for the final V2 application.
