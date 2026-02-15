"""
Test Suite for Master CV Save Reliability
Tests: YAML validation, timestamped backups, atomic writes, backup rotation.
"""
import unittest
import os
import sys
import time
import shutil

# Add root to path so we can import cv_bridge
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)

from cv_bridge import CVOrchestrator


class TestMasterCVEdit(unittest.TestCase):
    """Tests for CVOrchestrator.save_master_cv reliability features."""

    def setUp(self):
        """Create a clean test environment with a dummy Master CV."""
        self.orchestrator = CVOrchestrator()
        self.original_content = self.orchestrator.base_cv_path.read_text(encoding='utf-8')

        # Clean up any prior test backups
        if self.orchestrator.backups_dir.exists():
            for f in self.orchestrator.backups_dir.iterdir():
                if f.suffix == '.bak':
                    f.unlink()

    def tearDown(self):
        """Restore original Master CV content after each test."""
        self.orchestrator.base_cv_path.write_text(self.original_content, encoding='utf-8')

        # Clean up test backups
        if self.orchestrator.backups_dir.exists():
            for f in self.orchestrator.backups_dir.iterdir():
                if f.suffix == '.bak':
                    f.unlink()

    def test_valid_save_creates_backup(self):
        """Saving valid YAML should update the file and create a backup."""
        new_content = "cv:\n  name: Aaron Guo Updated\n"

        result = self.orchestrator.save_master_cv(new_content)
        self.assertTrue(result["success"], f"Save failed: {result}")

        # Verify file updated
        saved = self.orchestrator.base_cv_path.read_text(encoding='utf-8')
        self.assertEqual(saved, new_content)

        # Verify backup exists with ORIGINAL content
        backups = [f for f in self.orchestrator.backups_dir.iterdir() if f.suffix == '.bak']
        self.assertEqual(len(backups), 1, f"Expected 1 backup, found {len(backups)}")
        backup_content = backups[0].read_text(encoding='utf-8')
        self.assertEqual(backup_content, self.original_content)

    def test_invalid_yaml_rejected(self):
        """Invalid YAML should be rejected; file must remain untouched."""
        invalid_content = "cv:\n  name: [Unclosed list"

        result = self.orchestrator.save_master_cv(invalid_content)
        self.assertFalse(result["success"])
        self.assertIn("Invalid YAML", result["error"])

        # Verify file is UNTOUCHED
        current = self.orchestrator.base_cv_path.read_text(encoding='utf-8')
        self.assertEqual(current, self.original_content)

    def test_backup_rotation_keeps_last_5(self):
        """After 7 saves, only the 5 most recent backups should exist."""
        for i in range(7):
            time.sleep(1.1)  # Ensure timestamps differ (Windows has ~1s resolution)
            self.orchestrator.save_master_cv(f"cv:\n  update: {i}\n")

        backups = sorted(
            [f for f in self.orchestrator.backups_dir.iterdir() if f.suffix == '.bak'],
            key=lambda f: f.stat().st_mtime
        )
        self.assertEqual(len(backups), 5, f"Expected 5 backups, found {len(backups)}: {[b.name for b in backups]}")

    def test_load_master_cv(self):
        """load_job_cv('master_cv') should return the base CV content."""
        content = self.orchestrator.load_job_cv("master_cv")
        self.assertEqual(content, self.original_content)

    def test_save_job_cv_routes_master(self):
        """save_job_cv('master_cv', ...) should route to save_master_cv."""
        new_content = "cv:\n  name: Routed Save Test\n"
        result = self.orchestrator.save_job_cv("master_cv", new_content)

        # Should return a dict (from save_master_cv), not a string path
        self.assertIsInstance(result, dict)
        self.assertTrue(result["success"])

        saved = self.orchestrator.base_cv_path.read_text(encoding='utf-8')
        self.assertEqual(saved, new_content)


if __name__ == '__main__':
    unittest.main()
