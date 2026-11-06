# -*- coding: utf-8 -*-
import unittest
import threading
import time
import requests
import uvicorn
from datetime import datetime, timezone, timedelta

import database
import time_utils
from api import app

class ServerThread(threading.Thread):
    def __init__(self, app, host='127.0.0.1', port=8888):
        super().__init__()
        self.server = uvicorn.Server(uvicorn.Config(app, host=host, port=port, log_level="warning"))
        self.daemon = True

    def run(self):
        self.server.run()

    def stop(self):
        self.server.should_exit = True

class TestWutheringWavesPlatform(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        database.init_db()
        cls.server_thread = ServerThread(app, host='127.0.0.1', port=8888)
        cls.server_thread.start()
        time.sleep(1.5)
        cls.base_url = "http://127.0.0.1:8888"

    @classmethod
    def tearDownClass(cls):
        cls.server_thread.stop()

    def test_01_database_and_seed(self):
        content = database.get_all_content_data()
        self.assertIn("banner", content)
        self.assertIn("stygian", content)
        self.assertIn("spiral_abyss", content)
        self.assertIn("events", content)
        
        banner = content["banner"]
        self.assertIsNotNone(banner)
        self.assertIn("servers", banner)
        self.assertIn("asia", banner["servers"])
        self.assertIn("europe", banner["servers"])
        self.assertIn("america", banner["servers"])

    def test_02_time_calculation_exact_match(self):
        now = datetime.now(timezone.utc)
        target = now + timedelta(days=2, hours=3, minutes=4, seconds=5)
        
        result_str = time_utils.time_left_str(target, now)
        self.assertIn("2 يوم", result_str)
        self.assertIn("3 ساعة", result_str)
        self.assertIn("4 دقيقة", result_str)
        self.assertIn("5 ثانية", result_str)

        # Expired test
        past = now - timedelta(seconds=10)
        expired_str = time_utils.time_left_str(past, now)
        self.assertEqual(expired_str, "انتهى.")

    def test_03_health_endpoint(self):
        res = requests.get(f"{self.base_url}/api/health", timeout=5)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["database"], "connected")
        self.assertIn("utc_time", data)

    def test_04_content_endpoints(self):
        res_all = requests.get(f"{self.base_url}/api/content", timeout=5)
        self.assertEqual(res_all.status_code, 200)
        data = res_all.json()
        self.assertIn("banner", data)
        self.assertIn("events", data)

        res_banner = requests.get(f"{self.base_url}/api/content/banner", timeout=5)
        self.assertEqual(res_banner.status_code, 200)

        res_stygian = requests.get(f"{self.base_url}/api/content/stygian", timeout=5)
        self.assertEqual(res_stygian.status_code, 200)

        res_tower = requests.get(f"{self.base_url}/api/content/spiral_abyss", timeout=5)
        self.assertEqual(res_tower.status_code, 200)

        res_events = requests.get(f"{self.base_url}/api/content/events", timeout=5)
        self.assertEqual(res_events.status_code, 200)
        self.assertIsInstance(res_events.json(), list)

    def test_05_image_endpoints(self):
        # Banner image fallback / default
        res_img = requests.get(f"{self.base_url}/api/image/banner", timeout=5)
        self.assertEqual(res_img.status_code, 200)
        self.assertTrue(len(res_img.content) > 0)

        # Stygian image
        res_styg = requests.get(f"{self.base_url}/api/image/stygian", timeout=5)
        self.assertEqual(res_styg.status_code, 200)

        # Tower image
        res_tow = requests.get(f"{self.base_url}/api/image/spiral_abyss", timeout=5)
        self.assertEqual(res_tow.status_code, 200)

    def test_06_static_html_served(self):
        res = requests.get(f"{self.base_url}/", timeout=5)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Wuthering Waves Arabic", res.text)
        self.assertIn("telegram-web-app.js", res.text)

    def test_07_telegram_auth_verification(self):
        res = requests.post(
            f"{self.base_url}/api/auth/verify-telegram",
            json={"init_data": "invalid_data"},
            timeout=5
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("valid", data)

if __name__ == "__main__":
    unittest.main()
