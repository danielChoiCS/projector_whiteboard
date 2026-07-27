from src.vision.hand_tracker import _ensure_model


def test_ensure_model_downloads_when_missing(tmp_path):
    model_path = tmp_path / "models" / "hand_landmarker.task"
    calls = []

    def fake_downloader(url, dest):
        calls.append((url, dest))
        # Simulate the download actually producing a file, like urlretrieve does.
        with open(dest, "wb") as f:
            f.write(b"fake model bytes")

    result = _ensure_model(model_path, downloader=fake_downloader)

    assert result == model_path
    assert model_path.exists()
    assert len(calls) == 1


def test_ensure_model_skips_download_when_already_cached(tmp_path):
    model_path = tmp_path / "hand_landmarker.task"
    model_path.write_bytes(b"already cached")
    calls = []

    _ensure_model(model_path, downloader=lambda url, dest: calls.append((url, dest)))

    assert calls == []
