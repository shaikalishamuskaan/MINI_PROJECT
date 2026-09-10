from datetime import datetime

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
    pass

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )
    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="user",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="user",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="user",
    )


class Media(Base):
    __tablename__ = "media"

    id: Mapped[int] = mapped_column(primary_key=True)

    title: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
    )

    media_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )

    genre: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    release_year: Mapped[int] = mapped_column(
        nullable=False,
    )

    reviews: Mapped[list["Review"]] = relationship(
        back_populates="media",
    )

    favorites: Mapped[list["Favorite"]] = relationship(
        back_populates="media",
    )

    notifications: Mapped[list["Notification"]] = relationship(
        back_populates="media",
    )

class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media.id"),
        nullable=False,
    )

    rating: Mapped[int] = mapped_column(
        nullable=False,
    )

    comment: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="reviews",
    )

    media: Mapped["Media"] = relationship(
        back_populates="reviews",
    )

    __table_args__ = (
        UniqueConstraint(
            "user_id",
            "media_id",
            name="uq_review_user_media",
        ),
    )

class Favorite(Base):
    __tablename__ = "favorites"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        primary_key=True,
    )

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media.id"),
        primary_key=True,
    )

    user: Mapped["User"] = relationship(
        back_populates="favorites",
    )

    media: Mapped["Media"] = relationship(
        back_populates="favorites",
    )

class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )

    media_id: Mapped[int] = mapped_column(
        ForeignKey("media.id"),
        nullable=False,
    )

    message: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    is_read: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        nullable=False,
    )

    user: Mapped["User"] = relationship(
        back_populates="notifications",
    )

    media: Mapped["Media"] = relationship(
        back_populates="notifications",
    )

