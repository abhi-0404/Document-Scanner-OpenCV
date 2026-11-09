"""Tests for the Flask web interface in app.py."""
import io

import cv2
import pytest

import app as webapp


@pytest.fixture()
def client(tmp_path, monkeypatch):
    # Write scan results to a temp folder instead of the repo's "result images" folder.
    monkeypatch.setattr(webapp, "RESULT_FOLDER", str(tmp_path))
    webapp.app.config["TESTING"] = True
    return webapp.app.test_client()


def png_bytes(image) -> bytes:
    ok, buf = cv2.imencode(".png", image)
    assert ok
    return buf.tobytes()


def test_home_page_loads(client):
    assert client.get("/").status_code == 200


def test_upload_without_file_is_rejected(client):
    r = client.post("/api/upload", data={})
    assert r.status_code == 400
    assert r.get_json()["success"] is False


def test_upload_with_unsupported_type_is_rejected(client):
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"hello"), "notes.txt")}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert r.get_json()["error"] == "Unsupported file type"


def test_upload_with_corrupt_image_is_rejected(client):
    r = client.post("/api/upload", data={"file": (io.BytesIO(b"not really a png"), "page.png")}, content_type="multipart/form-data")
    assert r.status_code == 400
    assert r.get_json()["error"] == "Could not decode image"


def test_upload_scans_and_serves_the_result(client, photo, tmp_path):
    r = client.post("/api/upload", data={"file": (io.BytesIO(png_bytes(photo)), "page.png")}, content_type="multipart/form-data")
    assert r.status_code == 200
    body = r.get_json()
    assert body["success"] is True
    assert (tmp_path / body["resultFilename"]).is_file()

    served = client.get(body["result"])
    assert served.status_code == 200
    assert served.mimetype == "image/png"

    download = client.get(f"/api/download/{body['resultFilename']}")
    assert download.status_code == 200
    assert "attachment" in download.headers["Content-Disposition"]


def test_missing_result_is_404(client):
    assert client.get("/api/result/does-not-exist.png").status_code == 404
