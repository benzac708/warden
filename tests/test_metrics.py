import unittest

from warden import metrics


class TestMetrics(unittest.TestCase):
    def test_documented_counter_names_are_the_only_names(self):
        self.assertEqual(
            set(metrics._COUNTERS),
            {
                "warden_runs_total",
                "warden_failures_total",
                "warden_tokens_in_total",
                "warden_tokens_out_total",
            },
        )
        with self.assertRaises(KeyError):
            metrics.inc("runs")

    def test_render_uses_documented_names(self):
        metrics.inc("warden_runs_total")
        body = metrics.render()
        self.assertIn("warden_runs_total", body)
        self.assertIn("# TYPE warden_runs_total counter", body)


if __name__ == "__main__":
    unittest.main()
