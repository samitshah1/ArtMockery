import io
import json
import unittest

from fastapi.testclient import TestClient
from PIL import Image

from app import app


class AppSmokeTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_homepage_is_served(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response.headers["content-type"])
        self.assertIn("ArtMockery", response.text)

    def test_health_endpoint(self):
        response = self.client.get("/health")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "app": "ArtMockery"})

    def test_render_endpoint_returns_png(self):
        image_bytes = io.BytesIO()
        Image.new("RGB", (32, 32), "white").save(image_bytes, format="PNG")

        response = self.client.post(
            "/api/render",
            data={"settings": json.dumps({"outW": 800, "outH": 800, "texture": 0})},
            files={
                "painting": ("painting.png", image_bytes.getvalue(), "image/png"),
            },
        )

        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.headers["content-type"], "image/png")
        self.assertEqual(
            response.headers["content-disposition"],
            'attachment; filename="artmockery.png"',
        )
        with Image.open(io.BytesIO(response.content)) as rendered:
            self.assertEqual(rendered.size, (800, 800))


if __name__ == "__main__":
    unittest.main()
