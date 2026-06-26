from __future__ import annotations

from pathlib import Path
import time
from typing import Any, BinaryIO
from urllib.parse import urljoin

import requests

from berl.rate_limit import RateLimiter


BASE_URL = "https://ballchasing.com/api/"
FORBIDDEN_FILTERS = {"creator", "uploader"}
REPLAY_SORT_ALIASES = {"upload-date": "created"}


class BallchasingError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None, payload: Any = None) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.payload = payload


class BallchasingClient:
    def __init__(
        self,
        token: str,
        *,
        base_url: str = BASE_URL,
        session: requests.Session | None = None,
        limiter: RateLimiter | None = None,
    ) -> None:
        self.token = token
        self.base_url = base_url.rstrip("/") + "/"
        self.session = session or requests.Session()
        self.limiter = limiter or RateLimiter()

    @property
    def headers(self) -> dict[str, str]:
        return {"Authorization": self.token}

    def ping(self) -> dict[str, Any]:
        return self._request("GET", "", expected={200}, bucket=None)

    def list_groups(self, **params: Any) -> dict[str, Any]:
        params = self._owner_params(params, "creator")
        return self._request("GET", "groups", params=params, expected={200}, bucket="list")

    def list_replays(self, **params: Any) -> dict[str, Any]:
        params = self._owner_params(params, "uploader")
        if params.get("sort-by") in REPLAY_SORT_ALIASES:
            params["sort-by"] = REPLAY_SORT_ALIASES[str(params["sort-by"])]
        return self._request("GET", "replays", params=params, expected={200}, bucket="list")

    def get_group(self, group_id: str) -> dict[str, Any]:
        return self._request("GET", f"groups/{group_id}", expected={200}, bucket="mutation")

    def get_replay(self, replay_id: str) -> dict[str, Any]:
        return self._request("GET", f"replays/{replay_id}", expected={200}, bucket="mutation")

    def create_group(
        self,
        name: str,
        *,
        parent: str | None,
        player_identification: str,
        team_identification: str,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "name": name,
            "player_identification": player_identification,
            "team_identification": team_identification,
        }
        if parent:
            payload["parent"] = parent
        return self._request("POST", "groups", json=payload, expected={201}, bucket="mutation")

    def patch_group(self, group_id: str, fields: dict[str, Any]) -> None:
        self._request("PATCH", f"groups/{group_id}", json=fields, expected={204}, bucket="mutation")

    def delete_group(self, group_id: str) -> None:
        self._request("DELETE", f"groups/{group_id}", expected={204}, bucket="mutation")

    def patch_replay(self, replay_id: str, fields: dict[str, Any]) -> None:
        self._request("PATCH", f"replays/{replay_id}", json=fields, expected={204}, bucket="mutation")

    def delete_replay(self, replay_id: str) -> None:
        self._request("DELETE", f"replays/{replay_id}", expected={204}, bucket="mutation")

    def upload_replay(self, path: Path, *, visibility: str, group: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {"visibility": visibility}
        if group:
            params["group"] = group
        with path.open("rb") as handle:
            return self.upload_replay_file(handle, path.name, visibility=visibility, group=group)

    def upload_replay_file(
        self,
        handle: BinaryIO,
        filename: str,
        *,
        visibility: str,
        group: str | None,
    ) -> dict[str, Any]:
        params: dict[str, Any] = {"visibility": visibility}
        if group:
            params["group"] = group
        files = {"file": (filename, handle, "application/octet-stream")}
        return self._request(
            "POST",
            "v2/upload",
            params=params,
            files=files,
            expected={201, 409},
            bucket="mutation",
        )

    def _owner_params(self, params: dict[str, Any], owner_key: str) -> dict[str, Any]:
        cleaned = {key: value for key, value in params.items() if value not in (None, "", [])}
        for key in FORBIDDEN_FILTERS:
            cleaned.pop(key, None)
        cleaned[owner_key] = "me"
        return cleaned

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        files: dict[str, Any] | None = None,
        expected: set[int],
        bucket: str | None,
    ) -> Any:
        if bucket:
            self.limiter.wait(bucket)

        url = urljoin(self.base_url, path)
        response = self.session.request(method, url, headers=self.headers, params=params, json=json, files=files)
        if response.status_code == 429:
            time.sleep(1)
            if bucket:
                self.limiter.wait(bucket)
            response = self.session.request(method, url, headers=self.headers, params=params, json=json, files=files)

        if response.status_code not in expected:
            raise BallchasingError(self._error_message(response), response.status_code, self._response_payload(response))

        if response.status_code == 204 or not response.content:
            return None
        payload = self._response_payload(response)
        if response.status_code == 409 and isinstance(payload, dict):
            payload["_duplicate"] = True
        return payload

    def _response_payload(self, response: requests.Response) -> Any:
        try:
            return response.json()
        except ValueError:
            return response.text

    def _error_message(self, response: requests.Response) -> str:
        payload = self._response_payload(response)
        if isinstance(payload, dict):
            for key in ("error", "message"):
                if payload.get(key):
                    return f"ballchasing API returned {response.status_code}: {payload[key]}"
        if payload:
            return f"ballchasing API returned {response.status_code}: {payload}"
        return f"ballchasing API returned {response.status_code}"
