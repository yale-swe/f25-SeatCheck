# backend/src/app/api/auth.py
from __future__ import annotations

import base64
import json
import urllib.parse
import xml.etree.ElementTree as ET

import httpx
from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import RedirectResponse

from app.config import settings

router = APIRouter()

APP_BASE = settings.app_base
CAS_BASE = settings.cas_base
SERVICE_PATH = "/auth/cas/callback"
DEV_AUTH = settings.dev_auth  # True in dev, False in prod


def _service_url(request: Request) -> str:
    host = request.headers.get("host", "localhost:8000")
    scheme = "https" if request.url.scheme == "https" else "http"
    return f"{scheme}://{host}{SERVICE_PATH}"


@router.get("/auth/cas/login")
def cas_login(request: Request) -> RedirectResponse:
    svc = urllib.parse.quote(_service_url(request), safe="")
    return RedirectResponse(f"{CAS_BASE}/login?service={svc}", status_code=302)


@router.get(SERVICE_PATH)
async def cas_callback(request: Request, ticket: str) -> RedirectResponse:
    svc = urllib.parse.quote(_service_url(request), safe="")
    ticket_quoted = urllib.parse.quote(ticket, safe="")
    url = (
        f"{CAS_BASE}/p3/serviceValidate?service={svc}&ticket={ticket_quoted}"
    )
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
    if resp.status_code != 200:
        return RedirectResponse(url=f"{APP_BASE}/login?error=cas_http", status_code=302)

    ns = {"cas": "http://www.yale.edu/tp/cas"}
    try:
        root = ET.fromstring(resp.text)
        user_el = root.find(".//cas:authenticationSuccess/cas:user", ns)
        netid = (user_el.text or "").strip() if user_el is not None else ""
    except ET.ParseError:
        netid = ""

    if not netid:
        return RedirectResponse(
            url=f"{APP_BASE}/login?error=cas_failed", status_code=302
        )

    request.session["netid"] = netid
    return RedirectResponse(url=f"{APP_BASE}/", status_code=302)


@router.get("/auth/dev/login")
def dev_login(request: Request, netid: str = "dev001"):
    if not DEV_AUTH:
        raise HTTPException(status_code=404, detail="Disabled")
    request.session["netid"] = netid
    origin = request.headers.get("origin", "none")
    referer = request.headers.get("referer", "none")
    cookies = request.cookies
    print(f"[Auth] Dev login: set session netid={netid}")
    print(f"[Auth]   Origin: {origin}, Referer: {referer}")
    print(f"[Auth]   Cookies received: {list(cookies.keys())}")

    # For localhost dev, also return token in URL to bypass cookie issues
    # Frontend will extract this and store in localStorage
    token_data = {"netid": netid, "type": "dev"}
    token_json = json.dumps(token_data).encode()
    token_encoded = base64.urlsafe_b64encode(token_json).decode()
    token = token_encoded.rstrip("=")
    redirect_url = f"{APP_BASE}/?token={token}"
    print(f"[Auth]   Redirecting to {redirect_url}")
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    print(f"[Auth]   Session cookie will be set: seatcheck_session")
    return response


@router.post("/auth/dev/logout")
def dev_logout(request: Request):
    if not DEV_AUTH:
        raise HTTPException(status_code=404, detail="Disabled")
    request.session.clear()
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request):
    # Try to get netid from session cookie first
    netid = request.session.get("netid")

    # If no session, try Authorization header (for dev token-based auth)
    if not netid:
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header[7:]
            try:
                # Add padding if needed
                token += "=" * (4 - len(token) % 4)
                token_data = json.loads(base64.urlsafe_b64decode(token).decode())
                if token_data.get("type") == "dev" and "netid" in token_data:
                    netid = token_data["netid"]
                    print(f"[Auth]   Authenticated via token: {netid}")
            except Exception as e:
                print(f"[Auth]   Token decode error: {e}")

    origin = request.headers.get("origin", "none")
    cookies = request.cookies
    session_keys = list(request.session.keys())
    print(f"[Auth] /auth/me called:")
    print(f"[Auth]   netid={netid}")
    print(f"[Auth]   session_keys={session_keys}")
    print(f"[Auth]   origin={origin}")
    print(f"[Auth]   cookies_received={list(cookies.keys())}")
    auth_header_val = (
        "Bearer ..." if request.headers.get("authorization") else "none"
    )
    print(f"[Auth]   auth_header={auth_header_val}")
    if not netid:
        print(f"[Auth]   Not authenticated - no netid in session or token")
        raise HTTPException(status_code=401, detail="Not authenticated")
    print(f"[Auth]   Authenticated as {netid}")
    return {"netid": netid}


@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/debug/whoami")
def whoami(request: Request):
    return {
        "netid": request.session.get("netid"),
        "session_keys": list(request.session.keys()),
        "cookies": dict(request.cookies),
        "headers": {
            "origin": request.headers.get("origin"),
            "referer": request.headers.get("referer"),
            "host": request.headers.get("host"),
        }
    }
