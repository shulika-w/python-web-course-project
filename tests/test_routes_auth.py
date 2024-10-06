from unittest.mock import MagicMock

import pytest

from app.src.services.auth import auth_service


@pytest.mark.anyio
async def test_signup_user(client, user, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 201, response.text
    mock_add_task.assert_called_once()
    data = response.json()
    assert data["user"]["username"] == user.get("username")
    assert data["user"]["email"] == user.get("email")
    assert "id" in data["user"]
    assert (
        data["message"]
        == "The user successfully created. Check your email for confirmation"
    )


@pytest.mark.anyio
async def test_repeat_signup_user(client, user):
    response = await client.post(
        "/api/auth/signup",
        json=user,
    )
    assert response.status_code == 409, response.text
    data = response.json()
    assert data["detail"] == "The account already exists"


@pytest.mark.anyio
async def test_login_user_is_not_confirmed(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "The email is not confirmed"


@pytest.mark.anyio
async def test_request_password_reset_email_before_verification(
    client, user, monkeypatch
):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/password_reset_email",
        json={"email": user.get("email")},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_not_called()
    data = response.json()
    assert data["message"] == "Check your email for a password reset"


@pytest.mark.anyio
async def test_reset_password_before_verification(client, user):
    token = await auth_service.create_password_reset_token({"sub": user.get("email")})
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Reset password error"


@pytest.mark.anyio
async def test_set_password_before_verification(client, user, new_password):
    token = await auth_service.create_password_set_token({"sub": user.get("email")})
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Set password error"


@pytest.mark.anyio
async def test_request_verification_email(client, user, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/verification_email",
        json={"email": user.get("email")},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_called_once()
    data = response.json()
    assert data["message"] == "Check your email for confirmation"


@pytest.mark.anyio
async def test_request_verification_email_wrong_email(client, wrong_email, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/verification_email",
        json={"email": wrong_email},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_not_called()
    data = response.json()
    assert data["message"] == "Check your email for confirmation"


@pytest.mark.anyio
async def test_confirm_email_wrong_email_before_confirmation(client, wrong_email):
    token = await auth_service.create_email_verification_token({"sub": wrong_email})
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Verification error"


@pytest.mark.anyio
async def test_confirm_email_wrong_email_before_confirmation_custom_expire(
    client, wrong_email
):
    token = await auth_service.create_email_verification_token(
        {"sub": wrong_email}, expires_delta=100
    )
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Verification error"


@pytest.mark.anyio
async def test_confirm_email(client, user):
    token = await auth_service.create_email_verification_token(
        {"sub": user.get("email")}
    )
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "Email confirmed"


@pytest.mark.anyio
async def test_confirm_email_wrong_scope_token(client, user):
    token = await auth_service.create_access_token({"sub": user.get("email")})
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid scope for token"


@pytest.mark.anyio
async def test_repeat_confirm_email(client, user):
    token = await auth_service.create_email_verification_token(
        {"sub": user.get("email")}
    )
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "The email is already confirmed"


@pytest.mark.anyio
async def test_confirm_email_wrong_email_after_confirmation(client, wrong_email):
    token = await auth_service.create_email_verification_token({"sub": wrong_email})
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Verification error"


@pytest.mark.anyio
async def test_login_wrong_email(client, user, wrong_email):
    response = await client.post(
        "/api/auth/login",
        data={"username": wrong_email, "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.anyio
async def test_login_wrong_password(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": "password"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


@pytest.mark.anyio
async def test_login_user(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_refresh_token(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    token = data["refresh_token"]
    response = await client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_refresh_token_invalid(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    data = response.json()
    token = await auth_service.create_refresh_token(
        {"sub": user.get("email")}, expires_delta=100
    )
    response = await client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid refresh token"


@pytest.mark.anyio
async def test_refresh_token_wrong_email(client, wrong_email):
    token = await auth_service.create_refresh_token({"sub": wrong_email})
    response = await client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.anyio
async def test_refresh_token_wrong_email_custom_expire(client, wrong_email):
    token = await auth_service.create_refresh_token(
        {"sub": wrong_email}, expires_delta=100
    )
    response = await client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid email"


@pytest.mark.anyio
async def test_refresh_token_wrong_scope_token(client, user):
    token = await auth_service.create_access_token({"sub": user.get("email")})
    response = await client.get(
        "/api/auth/refresh_token",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid scope for token"


@pytest.mark.anyio
async def test_request_password_reset_email(client, user, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/password_reset_email",
        json={"email": user.get("email")},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_called_once()
    data = response.json()
    assert data["message"] == "Check your email for a password reset"


@pytest.mark.anyio
async def test_request_password_reset_email_wrong_email(
    client, wrong_email, monkeypatch
):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/password_reset_email",
        json={"email": wrong_email},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_not_called()
    data = response.json()
    assert data["message"] == "Check your email for a password reset"


@pytest.mark.anyio
async def test_reset_password_wrong_email_before_reset(client, wrong_email):
    token = await auth_service.create_password_reset_token({"sub": wrong_email})
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Reset password error"


@pytest.mark.anyio
async def test_reset_password_wrong_email_before_reset_custom_expire(
    client, wrong_email
):
    token = await auth_service.create_password_reset_token(
        {"sub": wrong_email}, expires_delta=100
    )
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Reset password error"


@pytest.mark.anyio
async def test_reset_password(client, user):
    token = await auth_service.create_password_reset_token({"sub": user.get("email")})
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["password_set_token"] is not None


@pytest.mark.anyio
async def test_login_user_password_reset_is_not_confirmed(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Password reset is not confirmed"


@pytest.mark.anyio
async def test_reset_password_wrong_email_after_reset(client, wrong_email):
    token = await auth_service.create_password_reset_token({"sub": wrong_email})
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Reset password error"


@pytest.mark.anyio
async def test_reset_password_wrong_scope_token(client, user):
    token = await auth_service.create_access_token({"sub": user.get("email")})
    response = await client.get(f"/api/auth/reset_password/{token}")
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid scope for token"


@pytest.mark.anyio
async def test_set_password_wrong_email_before_set(client, wrong_email, new_password):
    token = await auth_service.create_password_set_token({"sub": wrong_email})
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Set password error"


@pytest.mark.anyio
async def test_set_password_wrong_email_before_set_custom_expire(
    client, wrong_email, new_password
):
    token = await auth_service.create_password_set_token(
        {"sub": wrong_email}, expires_delta=100
    )
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Set password error"


@pytest.mark.anyio
async def test_request_verification_email_before_set(client, user, monkeypatch):
    mock_add_task = MagicMock()
    monkeypatch.setattr("fastapi.BackgroundTasks.add_task", mock_add_task)
    response = await client.post(
        "/api/auth/verification_email",
        json={"email": user.get("email")},
    )
    assert response.status_code == 200, response.text
    mock_add_task.assert_not_called()
    data = response.json()
    assert data["message"] == "The email is already confirmed"


@pytest.mark.anyio
async def test_confirm_email_before_set(client, user):
    token = await auth_service.create_email_verification_token(
        {"sub": user.get("email")}
    )
    response = await client.get(f"/api/auth/confirm_email/{token}")
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Verification error"


@pytest.mark.anyio
async def test_set_password(client, user, new_password):
    token = await auth_service.create_password_set_token({"sub": user.get("email")})
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["message"] == "The password has been reset"


@pytest.mark.anyio
async def test_set_password_wrong_email_after_set(client, wrong_email, new_password):
    token = await auth_service.create_password_set_token({"sub": wrong_email})
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 400, response.text
    data = response.json()
    assert data["detail"] == "Set password error"


@pytest.mark.anyio
async def test_set_password_wrong_scope_token(client, user, new_password):
    token = await auth_service.create_access_token({"sub": user.get("email")})
    response = await client.patch(
        f"/api/auth/set_password/{token}",
        json={"password": new_password},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid scope for token"


@pytest.mark.anyio
async def test_login_user_old_password(client, user):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": user.get("password")},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Invalid password"


@pytest.mark.anyio
async def test_login_user_new_password(client, user, new_password):
    response = await client.post(
        "/api/auth/login",
        data={"username": user.get("email"), "password": new_password},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["token_type"] == "bearer"


@pytest.mark.anyio
async def test_login_user_wrong_scope_token(client, user):
    token = await auth_service.create_refresh_token({"sub": user.get("email")})
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 401, response.text
    data = response.json()
    assert data["detail"] == "Could not validate credentials"


@pytest.mark.anyio
async def test_login_user_access_token_custom_expire(client, user, new_password):
    token = await auth_service.create_access_token(
        {"sub": user.get("email")}, expires_delta=100
    )
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == user.get("username")
    assert data["email"] == user.get("email")
    assert "id" in data


@pytest.mark.anyio
async def test_login_user_access_token(client, user):
    token = await auth_service.create_access_token({"sub": user.get("email")})
    response = await client.get(
        "/api/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["username"] == user.get("username")
    assert data["email"] == user.get("email")
    assert "id" in data