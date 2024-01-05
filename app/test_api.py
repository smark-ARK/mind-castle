from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from jose import jwt
from datetime import datetime, timedelta

from app.main import app, Base
from app.database import get_db
from app import config

client = TestClient(app)


def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World!"}


DTABASE_URL = config.settings.database_test_url

engine = create_engine(DTABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


def setup():
    Base.metadata.create_all(bind=engine)


# Test user data
test_user_data = {
    "username": "testuser",
    "email": "testuser@example.com",
    "password": "testpassword",
}

# Test note data
test_note_data = {"title": "Test Note", "detail": "Test Detail"}


def test_signup():
    response_signup = client.post(
        "/api/auth/signup",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
        },
    )
    client.post(
        "/api/auth/signup",
        json={
            "username": "testuser2",
            "email": "test@example2.com",
            "password": "testpassword",
        },
    )
    assert response_signup.status_code == 200
    user_data = response_signup.json()
    assert "id" in user_data


def test_login():
    response_login = client.post(
        "/api/auth/login", data={"username": "testuser", "password": "testpassword"}
    )
    assert response_login.status_code == 200
    token_data = response_login.json()
    assert "access_token" in token_data


def generate_valid_access_token(user_id: int, username: str) -> str:
    ALGORITHM = config.settings.algorithm
    SECRET_KEY = config.settings.secret_key

    to_encode = {
        "exp": datetime.utcnow()
        + timedelta(minutes=config.settings.access_expire_minutes),
        "user_id": user_id,
        "username": username,
    }
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def test_create_note():
    user_id = 1
    username = "testuser"

    access_token = generate_valid_access_token(user_id, username)

    note_data = {"title": "Test Note", "detail": "This is a test note."}

    response = client.post(
        "/api/notes",
        json=note_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200


def test_list_notes_no_auth():
    response_no_auth = client.get("/api/notes")
    assert response_no_auth.status_code == 401  # Unauthorized


def test_list_notes_with_auth():
    user_id = 1
    username = "testuser"

    access_token = generate_valid_access_token(user_id, username)
    headers = {"Authorization": f"Bearer {access_token}"}

    response_with_auth = client.get("/api/notes", headers=headers)
    assert response_with_auth.status_code == 200
    assert isinstance(response_with_auth.json(), list)


def test_get_note_with_auth():
    # Assuming you have a function generate_valid_access_token
    user_id = 1
    username = "testuser"
    access_token = generate_valid_access_token(user_id, username)
    headers = {"Authorization": f"Bearer {access_token}"}

    # Make a request to the /notes/{id} endpoint with a valid note ID and authentication
    note_id = 1
    response = client.get(f"/api/notes/{note_id}", headers=headers)

    # Check if the response status code is 200
    assert response.status_code == 200

    # Check if the response JSON contains the expected fields for a NoteResponse
    assert "note" in response.json()
    assert "participants" in response.json()
    assert "id" in response.json()["note"]
    assert "title" in response.json()["note"]
    assert "detail" in response.json()["note"]
    assert "owner" in response.json()["note"]
    assert "owner_id" in response.json()["note"]
    assert "created_at" in response.json()["note"]


def test_update_note():
    user_id = 1
    username = "testuser"

    access_token = generate_valid_access_token(user_id, username)

    note_id = 1
    updated_data = {"title": "Updated Note", "detail": "This note has been updated."}

    response = client.put(
        f"/api/notes/{note_id}",
        json=updated_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200


def test_delete_note():
    user_id = 1  # Replace with the actual user ID for testing
    username = "testuser"  # Replace with the actual username for testing

    access_token = generate_valid_access_token(user_id, username)

    note_id = 1

    response = client.delete(
        f"/api/notes/{note_id}", headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 204


def test_search_notes():
    user_id = 1  # Replace with the actual user ID for testing
    username = "testuser"  # Replace with the actual username for testing

    access_token = generate_valid_access_token(user_id, username)

    search_query = "test"

    response = client.get(
        f"/api/notes/search?q={search_query}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_share_note():
    user_id = 1
    username = "testuser"

    access_token = generate_valid_access_token(user_id, username)

    note_id = 1
    other_user_id = 2
    permission = "edit"

    share_data = {"user_id": other_user_id, "permission": permission}

    response = client.post(
        f"/api/notes/{note_id}/share",
        json=share_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200


def test_list_shared_notes():
    user_id = 2  # Replace with the actual user ID for testing
    username = "testuser2"  # Replace with the actual username for testing

    access_token = generate_valid_access_token(user_id, username)
    shared_user_id = 2
    shared_note_id = 1

    # Share a note with the authenticated user for testing
    share_data = {"user_id": shared_user_id, "permission": "read_only"}
    client.post(
        f"/api/notes/{shared_note_id}/share",
        json=share_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    response = client.get(
        "/api/notes/shared/", headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 200

    shared_notes = response.json()
    assert isinstance(shared_notes, list)
    assert len(shared_notes) > 0

    # Check if the shared note is in the list
    assert any(note["id"] == shared_note_id for note in shared_notes)


def teardown():
    Base.metadata.drop_all(bind=engine)


def test_update_note_by_owner():
    # Assume that the note with id=1 is owned by the current user
    note_id = 1
    access_token = generate_valid_access_token(user_id=1, username="testuser")
    headers = {"Authorization": f"Bearer {access_token}"}

    updated_note_data = {"title": "Updated Title", "detail": "Updated Detail"}
    response = client.put(
        f"/api/notes/{note_id}", json=updated_note_data, headers=headers
    )

    assert response.status_code == 200
    updated_note = response.json()
    assert updated_note["title"] == updated_note_data["title"]
    assert updated_note["detail"] == updated_note_data["detail"]


def test_update_note_by_shared_user_with_edit_permission():
    # Assume that the note with id=2 is shared with edit permission to the current user
    note_id = 1
    access_token = generate_valid_access_token(user_id=2, username="shared_user")
    headers = {"Authorization": f"Bearer {access_token}"}

    updated_note_data = {"title": "Updated Title", "detail": "Updated Detail"}
    response = client.put(
        f"/api/notes/{note_id}", json=updated_note_data, headers=headers
    )

    assert response.status_code == 200
    updated_note = response.json()
    assert updated_note["title"] == updated_note_data["title"]
    assert updated_note["detail"] == updated_note_data["detail"]


def test_update_permission():
    user_id = 1
    username = "testuser"

    access_token = generate_valid_access_token(user_id, username)

    note_id = 1
    other_user_id = 2
    new_permission = "read_only"

    share_data = {"user_id": other_user_id, "permission": new_permission}

    response = client.put(
        f"/api/notes/{note_id}/share",
        json=share_data,
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 200


def test_update_note_by_shared_user_without_edit_permission():
    # Assume that the note with id=3 is shared with read-only permission to the current user
    note_id = 1
    access_token = generate_valid_access_token(user_id=2, username="read_only_user")
    headers = {"Authorization": f"Bearer {access_token}"}

    updated_note_data = {"title": "Updated Title", "detail": "Updated Detail"}
    response = client.put(
        f"/api/notes/{note_id}", json=updated_note_data, headers=headers
    )

    assert (
        response.status_code == 403
    )  # Forbidden, as the user has read-only permission


def test_update_note_nonexistent_note():
    # Assume that the note with id=999 does not exist
    note_id = 999
    access_token = generate_valid_access_token(user_id=1, username="owner_user")
    headers = {"Authorization": f"Bearer {access_token}"}

    updated_note_data = {"title": "Updated Title", "detail": "Updated Detail"}
    response = client.put(
        f"/api/notes/{note_id}", json=updated_note_data, headers=headers
    )

    assert response.status_code == 404  # Not Found, as the note does not exist


def test_unshare_note():
    user_id = 1  # Replace with the actual user ID for testing
    username = "testuser"  # Replace with the actual username for testing

    access_token = generate_valid_access_token(user_id, username)

    note_id = 1
    other_user_id = 2

    response = client.delete(
        f"/api/notes/{note_id}/share?user_id={other_user_id}",
        headers={"Authorization": f"Bearer {access_token}"},
    )

    assert response.status_code == 204
