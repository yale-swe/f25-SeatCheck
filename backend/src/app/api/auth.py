# backend/src/app/api/auth.py
from __future__ import annotations

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
    url = f"{CAS_BASE}/p3/serviceValidate?service={svc}&ticket={urllib.parse.quote(ticket, safe='')}"
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
    return RedirectResponse(url=f"{APP_BASE}/", status_code=status.HTTP_302_FOUND)


@router.post("/auth/dev/logout")
def dev_logout(request: Request):
    if not DEV_AUTH:
        raise HTTPException(status_code=404, detail="Disabled")
    request.session.clear()
    return {"ok": True}


@router.get("/auth/me")
def me(request: Request):
    netid = request.session.get("netid")
    if not netid:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return {"netid": netid}


@router.post("/auth/logout")
def logout(request: Request):
    request.session.clear()
    return {"ok": True}


@router.get("/debug/whoami")
def whoami(request: Request):
    return {"netid": request.session.get("netid")}
