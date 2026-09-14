class Session:

    def __init__(self):
        self.user_id = None
        self.username = None

    @property
    def is_authenticated(self) -> bool:
        return self.user_id is not None

    def login(self, user) -> None:
        self.user_id = user.id
        self.username = user.username

    def logout(self) -> None:
        self.user_id = None
        self.username = None