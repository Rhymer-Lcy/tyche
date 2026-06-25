"""HTTP service layer — thin wrapper; verifies validation / dispatch / serialization (skipped if fastapi is absent)."""

import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from tyche.api import app  # noqa: E402

client = TestClient(app)

# golden chart: 1990-06-15 14:30 male, longitude 116.40 -> 庚午 壬午 辛亥 乙未 (辛 金 day)
CASE = {"datetime": "1990-06-15 14:30", "gender": "male", "longitude": 116.40}


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_chart_ok():
    r = client.post("/v1/chart", json=CASE)
    assert r.status_code == 200
    d = r.json()
    assert d["pillars"]["year"]["ganzhi"] == "庚午"
    assert d["pillars"]["day"]["ganzhi"] == "辛亥"
    assert d["pattern"]["pattern"] == "七杀格"
    assert d["config"]["reference_pillar"] == "day"


def test_reference_pillar_switch_changes_ten_gods():
    day = client.post("/v1/chart", json={**CASE, "reference_pillar": "day"}).json()
    year = client.post("/v1/chart", json={**CASE, "reference_pillar": "year"}).json()
    # 太极点 switch: the 十神 reference moves from the day stem to the year stem, so they must differ
    assert day["pillars"]["day"]["ten_gods"] != year["pillars"]["day"]["ten_gods"]
    assert year["config"]["reference_pillar"] == "year"


def test_reading_returns_prompt_and_report():
    r = client.post("/v1/reading", json={**CASE, "question": "事业财运"})
    assert r.status_code == 200
    d = r.json()
    assert set(d["prompt"]) == {"system", "user"}
    assert "事业财运" in d["prompt"]["user"]
    assert d["report"]["pattern"]["pattern"] == "七杀格"


def test_fleeting_single_year():
    r = client.post("/v1/fleeting", json={**CASE, "year": 2025})
    assert r.status_code == 200
    fy = r.json()["year"]
    assert fy["ganzhi"] == "乙巳" and fy["ten_gods"]["gan"] == "偏财"
    assert fy["dayun"] == "乙酉"


def test_fleeting_range():
    r = client.post("/v1/fleeting", json={**CASE, "year": 2024, "end_year": 2026})
    assert r.status_code == 200
    assert [f["ganzhi"] for f in r.json()["years"]] == ["甲辰", "乙巳", "丙午"]


def test_fleeting_with_months():
    r = client.post("/v1/fleeting", json={**CASE, "year": 2025, "with_months": True})
    assert r.status_code == 200
    d = r.json()
    assert d["year"]["ganzhi"] == "乙巳"
    assert len(d["months"]) == 12
    assert d["months"][0]["ganzhi"] == "戊寅"
    assert d["months"][0]["ten_gods"]["gan"] == "正印"


def test_bad_datetime_422():
    r = client.post("/v1/chart", json={**CASE, "datetime": "not-a-date"})
    assert r.status_code == 422


def test_bad_enum_422():
    r = client.post("/v1/chart", json={**CASE, "reference_pillar": "moon"})
    assert r.status_code == 422
