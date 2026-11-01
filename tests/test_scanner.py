import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from scanner import scan_directory

class TestScanDirectory(unittest.TestCase):
    """Tests for the read-only directory scanner."""

    def setUp(self) -> None:
        """Create a fresh temporary directory before each test."""
        self.temp_dir = TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.scan_root = Path(self.temp_dir.name)

    def test_empty_directory_returns_empty_list(self) -> None:
        """An empty directory should produce no file records."""
        result = scan_directory(self.scan_root)

        self.assertEqual(result, [])

    def test_three_files_at_limit_returns_all_records(self) -> None:
        (self.scan_root / "alpha.txt").touch()
        (self.scan_root / "beta.csv").touch()
        (self.scan_root / "gamma.md").touch()

        result = scan_directory(self.scan_root, 3)

        self.assertEqual(len(result), 3)

        actual_names = []

        for entry in result:
            actual_names.append(entry["name"])

        self.assertCountEqual(actual_names, ["alpha.txt", "beta.csv", "gamma.md"])

    def test_three_entries_over_limit_raises_value_error(self) -> None:
        (self.scan_root / "alpha.txt").touch()
        (self.scan_root / "beta.csv").touch()
        (self.scan_root / "gamma.md").touch()

        with self.assertRaises(ValueError):
            scan_directory(self.scan_root, 2)

    def test_three_files_below_limit_returns_all_records(self) -> None:
        (self.scan_root / "alpha.txt").touch()
        (self.scan_root / "beta.csv").touch()
        (self.scan_root / "gamma.md").touch()

        result = scan_directory(self.scan_root, 4)

        self.assertEqual(len(result), 3)

        actual_names = []

        for entry in result:
            actual_names.append(entry["name"])

        self.assertCountEqual(actual_names, ["alpha.txt", "beta.csv", "gamma.md"])

    def test_zero_limit_raises_value_error(self) -> None:
        with self.assertRaises(ValueError):
            scan_directory(self.scan_root, 0)

    def test_negative_limit_raises_value_error(self) -> None:
            with self.assertRaises(ValueError):
                scan_directory(self.scan_root, -1)

    def test_invalid_limit_types_raise_type_error(self) -> None:
        invalid_limits = ["3", 3.0, None, True, False]

        for invalid_limit in invalid_limits:
            with self.subTest(limit = invalid_limit):
                with self.assertRaises(TypeError):
                    scan_directory(self.scan_root, invalid_limit)

    def test_invalid_roots_raise_value_error(self) -> None:
        # Test missing root
        missing_root = self.scan_root / "missing"

        # Test regular-file root
        file_root = self.scan_root / "not_a_directory.txt"
        file_root.touch()

        # Test symbolic-link root
        symlink_root = self.scan_root / "linked_root"
        symlink_root.symlink_to(self.scan_root, target_is_directory=True)

        invalid_roots = [missing_root, file_root, symlink_root]

        for invalid_root in invalid_roots:
            with self.subTest(root=invalid_root):
                with self.assertRaises(ValueError):
                    scan_directory(invalid_root)


    def test_hidden_entry_counts_toward_limit_but_is_excluded(self) -> None:
        visible_entry = self.scan_root / "visible.txt"
        visible_entry.touch()
        hidden_entry = self.scan_root / ".hidden.txt"
        hidden_entry.touch()

        with self.assertRaises(ValueError):
            scan_directory(self.scan_root, 1)

        result = scan_directory(self.scan_root, 2)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "visible.txt")

    def test_directory_counts_toward_limit_but_is_excluded(self) -> None:
        visible = self.scan_root / "visible.txt"
        visible.touch()

        subfolder = self.scan_root / "subfolder"
        subfolder.mkdir()

        with self.assertRaises(ValueError):
            scan_directory(self.scan_root, 1)

        result = scan_directory(self.scan_root, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "visible.txt")

    def test_symlink_counts_toward_limit_but_is_excluded(self) -> None:
        visible = self.scan_root / "visible.txt"
        visible.touch()

        symlink_entry = self.scan_root/ "linked_visible.txt"
        symlink_entry.symlink_to(visible) 
        

        with self.assertRaises(ValueError):
            scan_directory(self.scan_root, 1)

        result = scan_directory(self.scan_root, 2)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "visible.txt")

    def test_nested_files_are_not_scanned(self) -> None:
        visible = self.scan_root / "visible.txt"
        visible.touch()

        subfolder = self.scan_root / "subfolder"
        subfolder.mkdir()

        nested = subfolder / "nested.txt"
        nested.touch()

        result = scan_directory(self.scan_root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "visible.txt")

    def test_empty_regular_file_is_included_with_zero_size(self) -> None:
        empty = self.scan_root / "empty.txt"
        empty.touch()

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "empty.txt")
        self.assertEqual(result[0]["size_bytes"], 1)

    def test_records_are_returned_in_filename_order(self) -> None:
        gamma = self.scan_root / "gamma.md"
        alpha = self.scan_root / "alpha.txt"
        beta = self.scan_root / "beta.csv"
        gamma.touch()
        alpha.touch()
        beta.touch()

        result = scan_directory(self.scan_root)

        sorted_files = []

        for file in result:
            sorted_files.append(file["name"])

        self.assertEqual(sorted_files, ["alpha.txt", "beta.csv", "gamma.md"])

    def test_file_record_contains_expected_fields(self) -> None:
        report = self.scan_root / "report.txt"
        report.touch()

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)
        record = result[0]

        key_set = set(record.keys())
        expected = set(["name", "extension", "size_bytes", "relative_path", "modified_time_ns"])

        self.assertSetEqual(key_set, expected)

    def test_uppercase_extension_is_normalized_to_lowercase(self)-> None:
        test = self.scan_root / "TEST.TXT"
        test.touch()

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["extension"], ".txt")

    def test_size_bytes_matches_fixture_content(self) -> None:
        content = b"Test"
        test = self.scan_root / "test.txt"
        test.write_bytes(content)

        expected_size = len(content)

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["size_bytes"], expected_size)

    def test_relative_path_is_relative_to_scan_root(self) -> None:
        test = self.scan_root / "test.txt"
        test.touch()

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["relative_path"], "test.txt")

    def test_modified_time_ns_matches_fixture_stat(self) -> None:
        test = self.scan_root / "test.txt"
        test.touch()

        mod_time = test.stat().st_mtime_ns
        result = scan_directory(self.scan_root)

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["modified_time_ns"], mod_time)

    def test_scan_does_not_modify_fixtures(self) -> None:
        content = b"Test"
        test = self.scan_root / "test.txt"
        test.write_bytes(content)
        linked_test = self.scan_root / "linked.txt"
        linked_test.symlink_to(test)

        before_names = set()

        for file in self.scan_root.iterdir():
            before_names.add(file.name)

        before_bytes = test.read_bytes()
        before_file_mtime = test.stat().st_mtime_ns
        before_link_mtime = linked_test.lstat().st_mtime_ns
        before_target = linked_test.readlink()

        result = scan_directory(self.scan_root)
        self.assertEqual(len(result), 1)

        after_names = set()
        for entry in self.scan_root.iterdir():
            after_names.add(entry.name)
        after_bytes = test.read_bytes()
        after_file_mtime = test.stat().st_mtime_ns
        after_link_mtime = linked_test.lstat().st_mtime_ns
        after_target = linked_test.readlink()

        self.assertSetEqual(before_names, after_names)
        self.assertEqual(before_bytes, after_bytes)
        self.assertEqual(before_file_mtime, after_file_mtime)
        self.assertEqual(before_link_mtime, after_link_mtime)
        self.assertEqual(before_target, after_target)

    def test_unreadable_metadata_warns_and_continues(self) -> None:
        alpha = self.scan_root / "alpha.txt"
        unreadable = self.scan_root / "beta.txt"
        gamma = self.scan_root / "gamma.txt"

        alpha.write_text("First valid file", encoding="utf-8")
        unreadable.write_text("Metadata will fail", encoding="utf-8")
        gamma.write_text("Last valid file", encoding="utf-8")

        original_stat = Path.stat
        original_is_file = Path.is_file
        original_is_symlink = Path.is_symlink

        unreadable_is_file = unreadable.is_file()
        unreadable_is_symlink = unreadable.is_symlink()
        error_message = "Simulated metadata failure"

        def selective_stat(
            path: Path, *, follow_symlinks: bool = True
        ):
            if path == unreadable:
                raise OSError(error_message)

            return original_stat(path, follow_symlinks=follow_symlinks)

        def selective_is_file(
            path: Path, *, follow_symlinks: bool = True
        ) -> bool:
            if path == unreadable:
                return unreadable_is_file

            return original_is_file(
                path, follow_symlinks=follow_symlinks
            )

        def selective_is_symlink(path: Path) -> bool:
            
            if path == unreadable:
                return unreadable_is_symlink

            return original_is_symlink(path)

        with (
            patch.object(
                Path,
                "stat",
                autospec=True,
                side_effect=selective_stat,
            ),
            patch.object(
                Path,
                "is_file",
                autospec=True,
                side_effect=selective_is_file,
            ),
            patch.object(
                Path,
                "is_symlink",
                autospec=True,
                side_effect=selective_is_symlink,
            ),
            patch("builtins.print") as mock_print,
        ):
            result = scan_directory(self.scan_root)

        actual_names = [record["name"] for record in result]

        self.assertEqual(actual_names, ["alpha.txt", "gamma.txt"])
        mock_print.assert_any_call(
            f"Skipped unreadable metadata: beta.txt ({error_message})"
        )

    def test_enumeration_stops_after_limit_plus_one_entries(self) -> None:
        limit = 3
        observed_entries: list[Path] = []

        
        available_entries = [
            self.scan_root / f"file_{index}.txt"
            for index in range(10)
        ]

        def controlled_iterator():
            for entry in available_entries:
                observed_entries.append(entry)
                yield entry

        with patch.object(
            Path,
            "iterdir",
            autospec=True,
            side_effect=lambda path: controlled_iterator(),
        ) as mock_iterdir:
            with self.assertRaisesRegex(
                ValueError,
                "exceeds the maximum allowed entry count",
            ):
                scan_directory(self.scan_root, limit=limit)

        mock_iterdir.assert_called_once_with(self.scan_root)
        self.assertEqual(len(observed_entries), limit + 1)
        self.assertEqual(
            observed_entries,
            available_entries[:limit + 1],
        )

