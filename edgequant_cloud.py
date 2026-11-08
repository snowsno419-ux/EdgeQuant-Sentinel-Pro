#!/usr/bin/env python3
"""Minimal Supabase Auth + PostgREST client for EdgeQuant Sentinel.

No service-role secret is accepted or stored. The desktop app uses only the
project's public anon key over HTTPS; Supabase RLS is the authorization boundary.
User access/refresh tokens are held in memory by the desktop app, not written to
an EdgeQuant settings file.
"""
from __future__ import annotations

import hashlib
import json
import os
import secrets
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone


class CloudError(RuntimeError):
    """Safe-to-display cloud/backend error (never includes an auth token)."""


class SupabaseClient:
    def __init__(self, url: str = "", anon_key: str = "", timeout: float = 20.0):
        self.url = (url or os.environ.get("EDGEQUANT_SUPABASE_URL", "")).strip().rstrip("/")
        self.anon_key = (anon_key or os.environ.get("EDGEQUANT_SUPABASE_ANON_KEY", "")).strip()
        self.timeout = max(5.0, float(timeout))
        if not self.url or not self.anon_key:
            raise CloudError("Cloud account is not configured. Follow SETUP.md to add the Supabase URL and anon key locally.")
        parsed_url = urllib.parse.urlsplit(self.url)
        local_hosts = {"localhost", "127.0.0.1", "::1"}
        local_http = parsed_url.scheme == "http" and (parsed_url.hostname or "").lower() in local_hosts
        if parsed_url.scheme != "https" and not local_http:
            raise CloudError("Supabase URL must use HTTPS (HTTP is allowed only for localhost development).")
        if parsed_url.username or parsed_url.password or parsed_url.query or parsed_url.fragment:
            raise CloudError("Use the clean Supabase Project URL only; do not put credentials/query strings in it.")
        if self.anon_key.lower().startswith(("sb_secret_", "service_role")):
            raise CloudError("A Supabase secret/service_role key is not allowed. Use the public anon/publishable key only.")
        # Traditional Supabase anon/service_role keys are JWTs. Reject the
        # privileged role defensively even if the key was renamed in a .env.
        jwt_parts = self.anon_key.split(".")
        if len(jwt_parts) == 3:
            try:
                import base64
                payload = jwt_parts[1] + "=" * (-len(jwt_parts[1]) % 4)
                claims = json.loads(base64.urlsafe_b64decode(payload.encode("ascii")))
                if str(claims.get("role") or "").lower() == "service_role":
                    raise CloudError("A Supabase service_role key is not allowed. Use the public anon key only.")
            except CloudError:
                raise
            except Exception:
                pass

    def _request(self, method: str, path: str, data=None, token: str = "", prefer: str = ""):
        url = self.url + "/" + path.lstrip("/")
        payload = None if data is None else json.dumps(data, ensure_ascii=False).encode("utf-8")
        headers = {"apikey": self.anon_key, "Accept": "application/json"}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        if token:
            headers["Authorization"] = "Bearer " + token
        else:
            headers["Authorization"] = "Bearer " + self.anon_key
        if prefer:
            headers["Prefer"] = prefer
        req = urllib.request.Request(url, data=payload, headers=headers, method=method.upper())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as response:
                body = response.read().decode("utf-8", errors="replace")
                if not body.strip():
                    return None
                try:
                    return json.loads(body)
                except json.JSONDecodeError:
                    return body
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            try:
                parsed = json.loads(body)
                msg = (parsed.get("msg") or parsed.get("message") or parsed.get("error_description")
                       or parsed.get("error") or str(parsed)) if isinstance(parsed, dict) else str(parsed)
            except Exception:
                msg = body or str(exc)
            raise CloudError(f"Supabase {exc.code}: {str(msg)[:500]}") from None
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            raise CloudError(f"Could not reach Supabase: {type(exc).__name__}: {exc}") from None

    @staticmethod
    def _user_session(payload):
        if not isinstance(payload, dict):
            return {}
        user = payload.get("user") or {}
        access = payload.get("access_token") or (payload.get("session") or {}).get("access_token")
        refresh = payload.get("refresh_token") or (payload.get("session") or {}).get("refresh_token")
        return {"access_token": str(access or ""), "refresh_token": str(refresh or ""),
                "user": user if isinstance(user, dict) else {}}

    def sign_up(self, email: str, password: str, role: str, display_name: str = "") -> dict:
        email = str(email or "").strip().lower()
        password = str(password or "")
        role = str(role or "").strip().lower()
        display_name = str(display_name or "").strip()[:100]
        if "@" not in email or len(email) > 320:
            raise CloudError("Enter a valid email address.")
        if len(password) < 10:
            raise CloudError("Use a password with at least 10 characters.")
        if role not in ("provider", "receiver"):
            raise CloudError("Choose Provider or Receiver.")
        payload = self._request("POST", "auth/v1/signup", {
            "email": email, "password": password,
            "data": {"role": role, "display_name": display_name},
        })
        return self._user_session(payload)

    def verify_email_otp(self, email: str, code: str) -> dict:
        email = str(email or "").strip().lower()
        code = str(code or "").strip().replace(" ", "")
        if "@" not in email:
            raise CloudError("Enter the email address used for registration.")
        if not code or len(code) > 32:
            raise CloudError("Enter the verification code from the email.")
        payload = self._request("POST", "auth/v1/verify", {
            "type": "signup", "email": email, "token": code,
        })
        session = self._user_session(payload)
        if not session.get("access_token"):
            raise CloudError("Email verified, but Supabase did not return a session. Sign in again.")
        return session

    def resend_confirmation(self, email: str) -> None:
        email = str(email or "").strip().lower()
        if "@" not in email:
            raise CloudError("Enter the email address used for registration.")
        self._request("POST", "auth/v1/resend", {"type": "signup", "email": email})

    def send_password_reset(self, email: str) -> None:
        email = str(email or "").strip().lower()
        if "@" not in email:
            raise CloudError("Enter a valid email address.")
        self._request("POST", "auth/v1/recover", {"email": email})

    def sign_in(self, email: str, password: str) -> dict:
        email = str(email or "").strip().lower()
        if not email or not str(password or ""):
            raise CloudError("Enter your email and password.")
        payload = self._request("POST", "auth/v1/token?grant_type=password",
                                {"email": email, "password": str(password)})
        session = self._user_session(payload)
        if not session.get("access_token"):
            raise CloudError("Sign-in did not return a session. Verify your email and try again.")
        return session

    def refresh_session(self, refresh_token: str) -> dict:
        if not refresh_token:
            raise CloudError("The session has expired; sign in again.")
        payload = self._request("POST", "auth/v1/token?grant_type=refresh_token",
                                {"refresh_token": str(refresh_token)})
        session = self._user_session(payload)
        if not session.get("access_token"):
            raise CloudError("The session could not be refreshed; sign in again.")
        return session

    def sign_out(self, access_token: str) -> None:
        if access_token:
            self._request("POST", "auth/v1/logout", token=access_token)

    def profile(self, session: dict) -> dict:
        user = session.get("user") or {}
        user_id = str(user.get("id") or "")
        if not user_id:
            raise CloudError("The signed-in user has no account ID.")
        query = urllib.parse.urlencode({"select": "id,display_name,role,created_at", "id": f"eq.{user_id}"})
        rows = self._request("GET", "rest/v1/profiles?" + query,
                             token=session.get("access_token", "")) or []
        if not isinstance(rows, list) or not rows:
            raise CloudError("Account profile is not ready. Check that the v1.9.12 Supabase schema/trigger is installed.")
        profile = rows[0]
        if profile.get("role") not in ("provider", "receiver"):
            raise CloudError("The account has no valid Provider/Receiver role.")
        return profile

    def list_groups(self, session: dict) -> list:
        query = urllib.parse.urlencode({
            "select": "id,name,description,visibility,owner_id,created_at",
            "order": "created_at.desc",
        })
        rows = self._request("GET", "rest/v1/provider_groups?" + query,
                             token=session.get("access_token", "")) or []
        return rows if isinstance(rows, list) else []

    def create_group(self, session: dict, name: str, description: str = "",
                     visibility: str = "private") -> dict:
        user_id = str((session.get("user") or {}).get("id") or "")
        name = str(name or "").strip()[:120]
        visibility = str(visibility or "private").lower()
        if not user_id or not name:
            raise CloudError("A signed-in provider and group name are required.")
        if visibility not in ("private", "public"):
            raise CloudError("Choose private or public visibility.")
        rows = self._request("POST", "rest/v1/provider_groups?select=*", {
            "owner_id": user_id, "name": name,
            "description": str(description or "").strip()[:500],
            "visibility": visibility,
        }, token=session.get("access_token", ""), prefer="return=representation") or []
        if not isinstance(rows, list) or not rows:
            raise CloudError("The group was not created. Check the installed schema and provider role.")
        return rows[0]

    def create_invite(self, session: dict, group_id: str, expires_days: int = 7) -> str:
        user_id = str((session.get("user") or {}).get("id") or "")
        raw = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        expires = (datetime.now(timezone.utc) + timedelta(days=max(1, min(90, int(expires_days)))))
        self._request("POST", "rest/v1/provider_group_invites", {
            "group_id": str(group_id), "created_by": user_id,
            "token_hash": token_hash, "expires_at": expires.isoformat(),
        }, token=session.get("access_token", ""), prefer="return=minimal")
        return raw

    def request_join_by_invite(self, session: dict, code: str) -> dict:
        code = str(code or "").strip()
        if len(code) < 20:
            raise CloudError("Invite code is too short or empty.")
        result = self._request("POST", "rest/v1/rpc/request_provider_invite",
                               {"p_token": code}, token=session.get("access_token", ""))
        return result if isinstance(result, dict) else {"group_id": result}

    def request_join(self, session: dict, group_id: str) -> dict:
        result = self._request("POST", "rest/v1/rpc/request_public_provider_group", {
            "p_group_id": str(group_id),
        }, token=session.get("access_token", ""))
        return result if isinstance(result, dict) else {"group_id": str(group_id), "status": "pending"}

    def list_join_requests(self, session: dict, group_id: str) -> list:
        query = urllib.parse.urlencode({
            "select": "id,group_id,requester_id,status,created_at",
            "group_id": f"eq.{group_id}", "status": "eq.pending", "order": "created_at.asc",
        })
        rows = self._request("GET", "rest/v1/provider_group_requests?" + query,
                             token=session.get("access_token", "")) or []
        return rows if isinstance(rows, list) else []

    def decide_join_request(self, session: dict, request_id: str, approved: bool) -> None:
        self._request("POST", "rest/v1/rpc/respond_provider_group_request", {
            "p_request_id": str(request_id), "p_approved": bool(approved),
        }, token=session.get("access_token", ""))

    def list_signals(self, session: dict, group_id: str, limit: int = 500) -> list:
        query = urllib.parse.urlencode({
            "select": "id,group_id,provider_id,symbol,direction,entry,stop_loss,take_profits,status,progress,payload,created_at,updated_at",
            "group_id": f"eq.{group_id}", "order": "created_at.desc",
            "limit": str(max(1, min(2000, int(limit)))),
        })
        rows = self._request("GET", "rest/v1/provider_signals?" + query,
                             token=session.get("access_token", "")) or []
        return rows if isinstance(rows, list) else []

    def create_signal(self, session: dict, group_id: str, signal: dict) -> dict:
        user_id = str((session.get("user") or {}).get("id") or "")
        body = {
            "group_id": str(group_id), "provider_id": user_id,
            "symbol": str(signal.get("symbol") or "")[:40],
            "direction": str(signal.get("direction") or "").upper(),
            "entry": signal.get("entry"), "stop_loss": signal.get("sl"),
            "take_profits": signal.get("tp_levels") or [],
            "status": "published", "payload": signal,
        }
        rows = self._request("POST", "rest/v1/provider_signals?select=*", body,
                             token=session.get("access_token", ""), prefer="return=representation") or []
        if not isinstance(rows, list) or not rows:
            raise CloudError("The cloud signal was not saved. Check the installed schema and group permissions.")
        return rows[0]

    def update_signal(self, session: dict, signal_id: str, patch: dict) -> None:
        query = urllib.parse.urlencode({"id": f"eq.{signal_id}"})
        self._request("PATCH", "rest/v1/provider_signals?" + query, patch,
                      token=session.get("access_token", ""), prefer="return=minimal")

    def add_signal_update(self, session: dict, signal_id: str, update_type: str,
                          details: dict | None = None) -> None:
        user_id = str((session.get("user") or {}).get("id") or "")
        self._request("POST", "rest/v1/provider_signal_updates", {
            "signal_id": str(signal_id), "provider_id": user_id,
            "update_type": str(update_type or "update")[:40],
            "details": details or {},
        }, token=session.get("access_token", ""), prefer="return=minimal")

    def list_group_signal_updates(self, session: dict, group_id: str, limit: int = 500) -> list:
        query = urllib.parse.urlencode({
            "select": "id,signal_id,group_id,provider_id,update_type,details,created_at",
            "group_id": f"eq.{group_id}", "order": "created_at.asc",
            "limit": str(max(1, min(2000, int(limit)))),
        })
        rows = self._request("GET", "rest/v1/provider_signal_updates?" + query,
                             token=session.get("access_token", "")) or []
        return rows if isinstance(rows, list) else []

    def list_signal_updates(self, session: dict, signal_id: str) -> list:
        query = urllib.parse.urlencode({
            "select": "id,update_type,details,created_at",
            "signal_id": f"eq.{signal_id}", "order": "created_at.asc", "limit": "100",
        })
        rows = self._request("GET", "rest/v1/provider_signal_updates?" + query,
                             token=session.get("access_token", "")) or []
        return rows if isinstance(rows, list) else []

    def delete_signal(self, session: dict, signal_id: str) -> None:
        query = urllib.parse.urlencode({"id": f"eq.{signal_id}"})
        self._request("DELETE", "rest/v1/provider_signals?" + query,
                      token=session.get("access_token", ""), prefer="return=minimal")


__all__ = ["CloudError", "SupabaseClient"]
