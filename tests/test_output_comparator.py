"""Tests for output comparator utilities."""

import csv
import tempfile
from pathlib import Path

import pytest

from src.utils.output_comparator import (
    ComparisonResult,
    CSVComparator,
    DifferenceType,
    OutputValidator,
    PDFComparator,
)


class TestCSVComparator:
    """Tests for CSV comparison functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.comparator = CSVComparator(tolerance=0.001)
        self.temp_dir = tempfile.mkdtemp()

    def _create_csv(self, filename: str, headers: list, rows: list) -> Path:
        """Helper to create a CSV file for testing."""
        path = Path(self.temp_dir) / filename
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def test_identical_csv_files(self):
        """Test comparison of identical CSV files."""
        headers = ["id", "name", "value"]
        rows = [
            ["1", "Alice", "100"],
            ["2", "Bob", "200"],
        ]
        source = self._create_csv("source.csv", headers, rows)
        target = self._create_csv("target.csv", headers, rows)

        report = self.comparator.compare(source, target)

        assert report.result == ComparisonResult.IDENTICAL
        assert report.similarity_score == 100.0
        assert len(report.differences) == 0

    def test_different_values(self):
        """Test detection of value differences."""
        headers = ["id", "name", "value"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "Alice", "100"], ["2", "Bob", "200"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "Alice", "100"], ["2", "Bob", "250"]],  # Different value
        )

        report = self.comparator.compare(source, target)

        # 1 of 6 cells different = 83.3% similarity → DIFFERENT (below 95% threshold)
        assert report.result == ComparisonResult.DIFFERENT
        assert any(d.diff_type == DifferenceType.VALUE_MISMATCH for d in report.differences)

    def test_missing_row(self):
        """Test detection of missing rows."""
        headers = ["id", "name"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "Alice"], ["2", "Bob"], ["3", "Charlie"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "Alice"], ["2", "Bob"]],  # Missing row 3
        )

        report = self.comparator.compare(source, target)

        assert any(d.diff_type == DifferenceType.MISSING_ROW for d in report.differences)
        assert report.metadata["source_row_count"] == 3
        assert report.metadata["target_row_count"] == 2

    def test_extra_row(self):
        """Test detection of extra rows."""
        headers = ["id", "name"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "Alice"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "Alice"], ["2", "Bob"]],  # Extra row
        )

        report = self.comparator.compare(source, target)

        assert any(d.diff_type == DifferenceType.EXTRA_ROW for d in report.differences)

    def test_column_mismatch(self):
        """Test detection of column differences."""
        source = self._create_csv(
            "source.csv",
            ["id", "name", "email"],
            [["1", "Alice", "alice@example.com"]],
        )
        target = self._create_csv(
            "target.csv",
            ["id", "name", "phone"],  # Different column
            [["1", "Alice", "555-1234"]],
        )

        report = self.comparator.compare(source, target)

        assert any(d.diff_type == DifferenceType.COLUMN_MISMATCH for d in report.differences)

    def test_numeric_tolerance(self):
        """Test numeric comparison with tolerance."""
        headers = ["id", "value"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "100.001"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "100.002"]],  # Within tolerance of 0.001
        )

        report = self.comparator.compare(source, target)

        # Should be identical since difference (0.001) equals tolerance
        assert report.result == ComparisonResult.IDENTICAL
        assert len(report.differences) == 0

    def test_case_insensitive_comparison(self):
        """Test case-insensitive string comparison."""
        headers = ["id", "name"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "ALICE"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "alice"]],  # Different case
        )

        comparator = CSVComparator(ignore_case=True)
        report = comparator.compare(source, target)

        assert report.result == ComparisonResult.IDENTICAL

    def test_whitespace_handling(self):
        """Test whitespace-insensitive comparison."""
        headers = ["id", "name"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "Alice"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "  Alice  "]],  # Extra whitespace
        )

        comparator = CSVComparator(ignore_whitespace=True)
        report = comparator.compare(source, target)

        assert report.result == ComparisonResult.IDENTICAL

    def test_key_based_comparison(self):
        """Test row matching by key columns."""
        headers = ["id", "name", "value"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "Alice", "100"], ["2", "Bob", "200"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["2", "Bob", "200"], ["1", "Alice", "100"]],  # Different order
        )

        report = self.comparator.compare(source, target, key_columns=["id"])

        assert report.result == ComparisonResult.IDENTICAL

    def test_date_comparison(self):
        """Test date value comparison across formats."""
        headers = ["id", "date"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "2024-01-15"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "01/15/2024"]],  # Different format
        )

        comparator = CSVComparator(date_formats=["%Y-%m-%d", "%m/%d/%Y"])
        report = comparator.compare(source, target)

        assert report.result == ComparisonResult.IDENTICAL

    def test_missing_file_error(self):
        """Test error handling for missing files."""
        source = Path(self.temp_dir) / "nonexistent.csv"
        target = self._create_csv("target.csv", ["id"], [["1"]])

        report = self.comparator.compare(source, target)

        assert report.result == ComparisonResult.ERROR
        assert "Failed to read" in report.error_message

    def test_similarity_score_calculation(self):
        """Test similarity score calculation."""
        headers = ["id", "a", "b", "c", "d"]
        source = self._create_csv(
            "source.csv",
            headers,
            [["1", "x", "y", "z", "w"]],
        )
        target = self._create_csv(
            "target.csv",
            headers,
            [["1", "x", "y", "z", "DIFFERENT"]],  # 1 of 5 different
        )

        report = self.comparator.compare(source, target)

        # 4 out of 5 cells match = 80%
        assert report.similarity_score == 80.0

    def test_empty_csv(self):
        """Test comparison with empty CSV files."""
        headers = ["id", "name"]
        source = self._create_csv("source.csv", headers, [])
        target = self._create_csv("target.csv", headers, [])

        report = self.comparator.compare(source, target)

        assert report.result == ComparisonResult.IDENTICAL


class TestPDFComparator:
    """Tests for PDF comparison functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.comparator = PDFComparator()
        self.temp_dir = tempfile.mkdtemp()

    def test_missing_source_file(self):
        """Test error handling for missing source file."""
        source = Path(self.temp_dir) / "nonexistent.pdf"
        target = Path(self.temp_dir) / "target.pdf"
        target.touch()

        report = self.comparator.compare(source, target)

        assert report.result == ComparisonResult.ERROR
        assert "not found" in report.error_message

    def test_missing_target_file(self):
        """Test error handling for missing target file."""
        source = Path(self.temp_dir) / "source.pdf"
        source.touch()
        target = Path(self.temp_dir) / "nonexistent.pdf"

        report = self.comparator.compare(source, target)

        assert report.result == ComparisonResult.ERROR
        assert "not found" in report.error_message

    def test_dependency_check(self):
        """Test that dependency check runs without error."""
        deps = self.comparator._check_dependencies()

        assert isinstance(deps, dict)
        assert "pillow" in deps
        assert "pdf2image" in deps
        assert "pdftoppm" in deps
        assert "pdftotext" in deps

    def test_identical_files_hash(self):
        """Test hash comparison of identical files."""
        # Create a simple binary file (not real PDF, but tests hash logic)
        content = b"%PDF-1.4 test content"
        source = Path(self.temp_dir) / "source.pdf"
        target = Path(self.temp_dir) / "target.pdf"
        source.write_bytes(content)
        target.write_bytes(content)

        # Use the public compare method which will fall back to hash
        comparator = PDFComparator(use_structural=False)
        report = comparator.compare(source, target)

        # Should be IDENTICAL since file contents are exactly the same
        # The comparison method may be hash or visual depending on available deps
        assert report.result == ComparisonResult.IDENTICAL
        assert report.similarity_score == 100.0

    def test_comparison_report_structure(self):
        """Test that comparison report has expected structure."""
        source = Path(self.temp_dir) / "source.pdf"
        source.write_bytes(b"%PDF test")
        target = Path(self.temp_dir) / "target.pdf"
        target.write_bytes(b"%PDF test 2")

        report = self.comparator.compare(source, target)

        assert hasattr(report, "source_file")
        assert hasattr(report, "target_file")
        assert hasattr(report, "comparison_type")
        assert hasattr(report, "result")
        assert hasattr(report, "similarity_score")
        assert hasattr(report, "differences")
        assert report.comparison_type == "pdf"


class TestOutputValidator:
    """Tests for the output validator orchestrator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = OutputValidator()
        self.temp_dir = tempfile.mkdtemp()

    def _create_csv(self, filename: str, headers: list, rows: list) -> Path:
        """Helper to create a CSV file for testing."""
        path = Path(self.temp_dir) / filename
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            writer.writerows(rows)
        return path

    def test_validate_conversion_csv_only(self):
        """Test validation with CSV files only."""
        headers = ["id", "name", "value"]
        rows = [["1", "Test", "100"]]
        crystal_csv = self._create_csv("crystal.csv", headers, rows)
        oracle_csv = self._create_csv("oracle.csv", headers, rows)

        results = self.validator.validate_conversion(
            crystal_csv=crystal_csv,
            oracle_csv=oracle_csv,
        )

        assert "csv" in results
        assert results["csv"].result == ComparisonResult.IDENTICAL

    def test_validate_conversion_no_files(self):
        """Test validation with no files provided."""
        results = self.validator.validate_conversion()

        assert len(results) == 0

    def test_generate_validation_report(self):
        """Test HTML report generation."""
        headers = ["id", "value"]
        crystal_csv = self._create_csv("crystal.csv", headers, [["1", "100"]])
        oracle_csv = self._create_csv("oracle.csv", headers, [["1", "100"]])

        comparisons = self.validator.validate_conversion(
            crystal_csv=crystal_csv,
            oracle_csv=oracle_csv,
        )

        output_dir = Path(self.temp_dir) / "reports"
        report_path = self.validator.generate_validation_report(
            "TestReport",
            comparisons,
            output_dir,
        )

        assert report_path.exists()
        content = report_path.read_text()
        assert "TestReport" in content
        assert "PASS" in content or "FAIL" in content
        assert "CSV" in content.upper()

    def test_batch_validate(self):
        """Test batch validation of multiple reports."""
        headers = ["id", "value"]

        validations = []
        for i in range(3):
            crystal = self._create_csv(f"crystal_{i}.csv", headers, [[str(i), "100"]])
            oracle = self._create_csv(f"oracle_{i}.csv", headers, [[str(i), "100"]])
            validations.append(
                {
                    "name": f"Report_{i}",
                    "crystal_csv": str(crystal),
                    "oracle_csv": str(oracle),
                }
            )

        output_dir = Path(self.temp_dir) / "batch_reports"
        results = self.validator.batch_validate(validations, output_dir)

        assert len(results) == 3
        assert all(r["overall_pass"] for r in results)
        assert all(Path(r["report_path"]).exists() for r in results)

    def test_is_acceptable_property(self):
        """Test is_acceptable property on comparison reports."""
        headers = ["id", "value"]
        crystal = self._create_csv("crystal.csv", headers, [["1", "100"]])
        oracle = self._create_csv("oracle.csv", headers, [["1", "100"]])

        results = self.validator.validate_conversion(
            crystal_csv=crystal,
            oracle_csv=oracle,
        )

        assert results["csv"].is_acceptable is True

    def test_comparison_report_to_dict(self):
        """Test serialization of comparison report."""
        headers = ["id"]
        crystal = self._create_csv("crystal.csv", headers, [["1"]])
        oracle = self._create_csv("oracle.csv", headers, [["1"]])

        results = self.validator.validate_conversion(
            crystal_csv=crystal,
            oracle_csv=oracle,
        )

        report_dict = results["csv"].to_dict()

        assert "source_file" in report_dict
        assert "target_file" in report_dict
        assert "result" in report_dict
        assert "similarity_score" in report_dict
        assert "differences" in report_dict
        assert "timestamp" in report_dict


class TestDifference:
    """Tests for the Difference dataclass."""

    def test_difference_to_dict(self):
        """Test serialization of difference."""
        from src.utils.output_comparator import Difference

        diff = Difference(
            diff_type=DifferenceType.VALUE_MISMATCH,
            location="row 1, col 'name'",
            expected="Alice",
            actual="Bob",
            severity="warning",
            details="Name changed",
        )

        d = diff.to_dict()

        assert d["type"] == "value_mismatch"
        assert d["location"] == "row 1, col 'name'"
        assert d["expected"] == "Alice"
        assert d["actual"] == "Bob"
        assert d["severity"] == "warning"
        assert d["details"] == "Name changed"
