"""Miroir de ``web/src/lib/queueSync.ts`` — fusion résumé → file."""

from __future__ import annotations


def _path_key(source_path: str) -> str:
    return source_path


def _merge_summary_into_queue(queue: dict, summary_records: list[dict]) -> dict:
    by_path = {_path_key(r["sourcePath"]): r for r in summary_records}
    merged = []
    for item in queue["items"]:
        merged.append(by_path.get(_path_key(item["sourcePath"]), item))
    for rec in summary_records:
        key = _path_key(rec["sourcePath"])
        if not any(_path_key(i["sourcePath"]) == key for i in merged):
            merged.append(rec)
    return {**queue, "items": merged}


def test_count_conversion_results() -> None:
    items = [
        {"status": "success"},
        {"status": "success_review"},
        {"status": "error"},
        {"status": "queued"},
    ]
    ok = sum(1 for i in items if i["status"] in ("success", "success_review", "success_fallback"))
    err = sum(1 for i in items if i["status"] in ("error", "empty"))
    assert ok == 2
    assert err == 1


def test_merge_updates_status_label() -> None:
    queue = {
        "schemaVersion": "0",
        "items": [
            {
                "sourcePath": "/tmp/a.txt",
                "status": "queued",
                "statusLabel": "En attente",
            }
        ],
        "outputDir": "/tmp/out",
        "canStartConversion": True,
        "totalSizeLabel": "1 o",
    }
    summary_records = [
        {
            "sourcePath": "/tmp/a.txt",
            "status": "success",
            "statusLabel": "OK",
            "progressPercent": 1.0,
        }
    ]
    out = _merge_summary_into_queue(queue, summary_records)
    assert out["items"][0]["status"] == "success"
    assert out["items"][0]["statusLabel"] == "OK"
