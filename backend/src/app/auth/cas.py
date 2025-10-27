import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse
from app.config import settings
from typing import Any

router = APIRouter()


@router.get("/cas")
async def cas_login(
    request: Request, ticket: str | None = None, redirect: str | None = None
) -> Any:
    """
    Entry point for CAS login. Redirects to Yale CAS if no ticket is provided.
    After CAS redirects back, we verify the ticket and store session data.
    """
    service_url = str(request.url_for("cas_login"))

    # if user coming back with CAS ticket → verify
    if ticket:
        validate_url = f"{settings.cas_base_url}/serviceValidate"
        params = {"service": service_url, "ticket": ticket}
        async with httpx.AsyncClient() as client:
            response = await client.get(validate_url, params=params)

        if "authenticationSuccess" in response.text:
            # extr user NetID
            import re

            match = re.search(r"<cas:user>(.*?)</cas:user>", response.text)
            netid = match.group(1) if match else None

            if netid:
                # save user session
                request.session["user"] = {"netid": netid}
                redirect_url = redirect or "/check"
                return RedirectResponse(url=redirect_url)

        return JSONResponse({"error": "CAS authentication failed"}, status_code=401)

    # no ticket → redirect to Yale CAS
    cas_login_url = f"{settings.cas_base_url}/login?service={service_url}"
    return RedirectResponse(url=cas_login_url)


# check if user is authenticated
@router.get("/check")
async def check_auth(request: Request) -> dict[str, bool]:
    user = request.session.get("user")
    if user:
        return {"auth": True, "user": user}
    return {"auth": False}


# log out
@router.get("/logout")
async def logout(request: Request) -> dict[str, bool]:
    request.session.clear()
    return {"success": True}
