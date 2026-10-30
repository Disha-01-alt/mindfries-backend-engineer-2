"""API tests. They exercise the FastAPI edge via TestClient, but skip cleanly
when FastAPI/httpx aren't installed — so ``python3 -m unittest`` grades the core
engine with or without the web dependencies present."""

import unittest

try:
    from fastapi.testclient import TestClient

    from alive.api.app import create_app
    from alive.api.deps import reset_engine

    _HAVE_FASTAPI = True
except Exception:  # pragma: no cover - import guard
    _HAVE_FASTAPI = False


@unittest.skipUnless(_HAVE_FASTAPI, "fastapi/httpx not installed")
class TestApi(unittest.TestCase):
    def setUp(self):
        reset_engine()  # fresh, seeded engine per test
        self.client = TestClient(create_app())

    def test_healthz(self):
        r = self.client.get("/healthz")
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.json()["status"], "ok")

    def test_seeded_member_has_a_score_with_lineage(self):
        r = self.client.get("/members/m_risk/score")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["member_id"], "m_risk")
        self.assertIn(body["band"], {"low", "moderate", "high", "critical"})
        self.assertTrue(body["contributions"])  # lineage present

    def test_unknown_member_score_is_404(self):
        self.assertEqual(self.client.get("/members/ghost/score").status_code, 404)

    def test_enroll_register_ingest_flow(self):
        self.assertEqual(self.client.post("/members", json={"member_id": "api1", "name": "API One", "chronological_age": 40}).status_code, 201)
        self.assertEqual(
            self.client.post("/members/api1/devices", json={"device_id": "api1_band", "source": "goqii_band", "kind": "band"}).status_code,
            201,
        )
        r = self.client.post("/ingest", json={
            "member_id": "api1", "device_id": "api1_band", "metric": "steps",
            "event_time": 1000.0, "value": 2000, "unit": "count", "seq": 1, "source": "goqii_band",
        })
        self.assertEqual(r.status_code, 200)
        self.assertEqual(self.client.get("/members/api1/score").status_code, 200)

    def test_bad_unit_is_domain_400(self):
        self.client.post("/members", json={"member_id": "api2", "name": "API Two", "chronological_age": 40})
        self.client.post("/members/api2/devices", json={"device_id": "api2_band", "source": "goqii_band", "kind": "band"})
        r = self.client.post("/ingest", json={
            "member_id": "api2", "device_id": "api2_band", "metric": "blood_glucose",
            "event_time": 1000.0, "value": 6.0, "unit": "mmHg", "seq": 1, "source": "goqii_band",
        })
        self.assertEqual(r.status_code, 400)
        self.assertEqual(r.json()["code"], "unit_mismatch")

    def test_cohort_summary(self):
        r = self.client.post("/cohorts/summary", json={"member_ids": ["m_fit", "m_drift", "m_risk"]})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["size"], 3)
        self.assertEqual(body["scored"], 3)

    def test_aging_endpoint(self):
        r = self.client.get("/members/m_fit/aging")
        self.assertEqual(r.status_code, 200)
        self.assertIn("biological_age", r.json())


if __name__ == "__main__":
    unittest.main()
