import os
import unittest
from unittest.mock import patch

from warden.config import Config


class TestConfig(unittest.TestCase):
    @patch.dict(os.environ, {}, clear=True)
    def test_agent_requires_the_key(self):
        with self.assertRaises(RuntimeError):
            Config.from_env()

    @patch.dict(os.environ, {}, clear=True)
    def test_showcase_does_not_require_the_key(self):
        cfg = Config.from_env(require_key=False)
        self.assertEqual(cfg.llm_model, "llama-3.1-8b-instant")
        self.assertEqual(cfg.llm_base_url, "https://api.groq.com/openai/v1")


if __name__ == "__main__":
    unittest.main()
