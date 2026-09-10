from pathlib import Path

from scripts import release


def test_distribute_apk_creates_identical_aliases(tmp_path, monkeypatch):
    source = tmp_path / "signed.apk"
    source.write_bytes(b"signed-apk-fixture")
    downloads = tmp_path / "downloads"
    monkeypatch.setattr(release, "STATIC_DOWNLOAD_DIR", str(downloads))

    targets = release.distribute_apk(str(source), "9.8.7")

    assert [path.name for path in targets] == [
        "序时_v9.8.7.apk",
        "序时.apk",
        "ClassSchedule.apk",
        "时序_v9.8.7.apk",
        "时序.apk",
    ]
    assert {Path(path).read_bytes() for path in targets} == {source.read_bytes()}
    assert len({release.calc_sha256(path) for path in targets}) == 1
