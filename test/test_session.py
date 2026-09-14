from types import SimpleNamespace

from app.session import Session


def test_session_login():
    session = Session()

    user = SimpleNamespace(
        id=1,
        username="alice",
    )

    session.login(user)

    assert session.user_id == 1
    assert session.username == "alice"
    assert session.is_authenticated is True


def test_session_logout():
    session = Session()

    user = SimpleNamespace(
        id=1,
        username="alice",
    )

    session.login(user)
    session.logout()

    assert session.user_id is None
    assert session.username is None
    assert session.is_authenticated is False


def test_new_session_is_not_authenticated():
    session = Session()

    assert session.is_authenticated is False