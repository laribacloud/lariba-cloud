import time
import uuid

import pytest
from httpx import AsyncClient

# Adjust if your FastAPI app lives somewhere else
from src.main import app


BASE = "http://test"


@pytest.mark.asyncio
async def test_invite_resend_rotates_token_and_old_token_fails():
    """
    Flow:
    - login as owner
    - get org_id
    - create invite -> get invite_id + old_token
    - resend -> get new_token (different)
    - register+login as invited user
    - accept with old token => 403
    - accept with new token => 200
    - accept again => 409
    """

    owner_email = "you@example.com"
    owner_password = "supersecret123"

    async with AsyncClient(app=app, base_url=BASE) as ac:
        # login owner
        r = await ac.post(
            "/v1/auth/login",
            data={"username": owner_email, "password": owner_password},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, r.text
        owner_token = r.json()["access_token"]
        owner_headers = {"Authorization": f"Bearer {owner_token}"}

        # list orgs
        r = await ac.get("/v1/organizations", headers=owner_headers)
        assert r.status_code == 200, r.text
        orgs = r.json()
        assert isinstance(orgs, list) and len(orgs) > 0
        org_id = orgs[0]["id"]

        # create a unique invite email
        ts = int(time.time())
        email = f"resendtest+{ts}@example.com"

        r = await ac.post(
            f"/v1/organizations/{org_id}/invites",
            headers=owner_headers,
            json={"email": email, "role": "member"},
        )
        assert r.status_code == 200, r.text
        inv = r.json()
        invite_id = inv["id"]
        old_token = inv["token"]

        # resend (rotate token)
        r = await ac.post(
            f"/v1/organizations/invites/{invite_id}/resend",
            headers=owner_headers,
        )
        assert r.status_code == 200, r.text
        res = r.json()
        new_token = res["token"]
        assert new_token != old_token

        # register invitee (ignore if already exists)
        r = await ac.post(
            "/v1/auth/register",
            json={"email": email, "password": "supersecret123", "name": "Resend Test"},
        )
        assert r.status_code in (200, 409), r.text

        # login invitee
        r = await ac.post(
            "/v1/auth/login",
            data={"username": email, "password": "supersecret123"},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        assert r.status_code == 200, r.text
        invitee_token = r.json()["access_token"]
        invitee_headers = {"Authorization": f"Bearer {invitee_token}"}

        # accept with OLD token -> 403
        r = await ac.post(
            f"/v1/organizations/invites/{invite_id}/accept",
            headers=invitee_headers,
            params={"token": old_token},
        )
        assert r.status_code == 403, r.text

        # accept with NEW token -> 200
        r = await ac.post(
            f"/v1/organizations/invites/{invite_id}/accept",
            headers=invitee_headers,
            params={"token": new_token},
        )
        assert r.status_code == 200, r.text
        assert r.json()["status"] == "accepted"

        # accept again -> 409
        r = await ac.post(
            f"/v1/organizations/invites/{invite_id}/accept",
            headers=invitee_headers,
            params={"token": new_token},
        )
        assert r.status_code == 409, r.text