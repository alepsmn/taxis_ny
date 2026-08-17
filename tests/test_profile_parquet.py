import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from scripts.profile_parquet import (
    build_passenger_count_metrics,
    calculate_percentage,
    main,
)


class CalculatePercentageTests(unittest.TestCase):
    def test_calculates_and_rounds_percentage(self) -> None:
        self.assertEqual(calculate_percentage(1, 3), 33.333333)

    def test_empty_total_returns_zero(self) -> None:
        self.assertEqual(calculate_percentage(0, 0), 0.0)


class PassengerCountMetricsTests(unittest.TestCase):
    def test_builds_range_and_negative_row_metrics(self) -> None:
        frequency_rows = [
            (None, 2),
            (-2, 3),
            (-1, 4),
            (0, 5),
            (2, 6),
        ]

        metrics = build_passenger_count_metrics(
            frequency_rows,
            row_count=20,
        )

        self.assertEqual(metrics["minimum"], -2)
        self.assertEqual(metrics["maximum"], 2)
        self.assertEqual(metrics["negative_count"], 7)
        self.assertEqual(metrics["negative_percentage"], 35.0)

    def test_all_null_values_have_no_observed_range(self) -> None:
        metrics = build_passenger_count_metrics(
            [(None, 3)],
            row_count=3,
        )

        self.assertIsNone(metrics["minimum"])
        self.assertIsNone(metrics["maximum"])
        self.assertEqual(metrics["negative_count"], 0)
        self.assertEqual(metrics["negative_percentage"], 0.0)


class MainTests(unittest.TestCase):
    def test_hash_mismatch_has_no_stdout_and_returns_failure(self) -> None:
        with tempfile.NamedTemporaryFile() as parquet_file:
            stdout = io.StringIO()
            stderr = io.StringIO()

            with redirect_stdout(stdout), redirect_stderr(stderr):
                exit_code = main(
                    [
                        str(Path(parquet_file.name)),
                        "--expected-sha256",
                        "0" * 64,
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout.getvalue(), "")
        self.assertIn("SHA-256 incorrecto", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
