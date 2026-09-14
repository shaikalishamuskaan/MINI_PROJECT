import bcrypt

from app.repo import UserRepository


class AuthService:

    def __init__(
        self,
        user_repository: UserRepository,
    ):
        self.user_repository = user_repository

    async def login(
        self,
        username: str,
        password: str,
    ):
        if not username.strip():
            raise ValueError(
                "Username cannot be empty."
            )

        if not password:
            raise ValueError(
                "Password cannot be empty."
            )

        user = (
            await self.user_repository
            .get_user_by_username(
                username.strip()
            )
        )

        if user is None:
            raise ValueError(
                "Invalid username or password."
            )

        password_matches = bcrypt.checkpw(
            password.encode("utf-8"),
            user.password_hash.encode("utf-8"),
        )

        if not password_matches:
            raise ValueError(
                "Invalid username or password."
            )

        return user