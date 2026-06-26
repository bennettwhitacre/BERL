from pathlib import Path

import pytest
import responses

from berl.api import BASE_URL, BallchasingClient, BallchasingError


@responses.activate
def test_list_groups_forces_creator_me() -> None:
    responses.get(f"{BASE_URL}groups", json={"list": []}, status=200)
    client = BallchasingClient("token")

    client.list_groups(creator="someone-else", uploader="bad", count=200)

    request = responses.calls[0].request
    assert request.headers["Authorization"] == "token"
    assert "creator=me" in request.url
    assert "uploader=" not in request.url
    assert "someone-else" not in request.url


@responses.activate
def test_list_replays_forces_uploader_me() -> None:
    responses.get(f"{BASE_URL}replays", json={"list": []}, status=200)
    client = BallchasingClient("token")

    client.list_replays(uploader="someone-else", creator="bad", count=200)

    request = responses.calls[0].request
    assert request.headers["Authorization"] == "token"
    assert "uploader=me" in request.url
    assert "creator=" not in request.url
    assert "someone-else" not in request.url


@responses.activate
def test_list_replays_maps_upload_date_sort_to_created() -> None:
    responses.get(f"{BASE_URL}replays", json={"list": []}, status=200)
    client = BallchasingClient("token")

    client.list_replays(**{"sort-by": "upload-date", "sort-dir": "desc"})

    request = responses.calls[0].request
    assert "sort-by=created" in request.url
    assert "upload-date" not in request.url


@responses.activate
def test_patch_replay_expects_204() -> None:
    responses.patch(f"{BASE_URL}replays/replay-1", status=204)
    client = BallchasingClient("token")

    client.patch_replay("replay-1", {"visibility": "private"})

    assert responses.calls[0].request.body == b'{"visibility": "private"}'


@responses.activate
def test_upload_treats_409_as_duplicate_success(tmp_path: Path) -> None:
    replay = tmp_path / "game.replay"
    replay.write_bytes(b"replay")
    responses.post(f"{BASE_URL}v2/upload", json={"id": "existing"}, status=409)
    client = BallchasingClient("token")

    result = client.upload_replay(replay, visibility="public", group="group-1")

    assert result["id"] == "existing"
    assert result["_duplicate"] is True
    request = responses.calls[0].request
    assert "visibility=public" in request.url
    assert "group=group-1" in request.url


@responses.activate
def test_error_includes_status() -> None:
    responses.get(f"{BASE_URL}groups", json={"error": "nope"}, status=403)
    client = BallchasingClient("token")

    with pytest.raises(BallchasingError) as exc:
        client.list_groups()

    assert exc.value.status_code == 403
    assert "nope" in str(exc.value)
