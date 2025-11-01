import unittest
import tempfile
import os
from pathlib import Path
from datetime import date

# This import will fail until we create mcp_server.py
from mcp_server import query_tasks
from task_tool import TaskStatus, TaskPriority

class TestMCPServer(unittest.TestCase):

    def setUp(self):
        """Set up a temporary vault with test data before each test."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = self.temp_dir.name
        
        # Create some test files
        content1 = """
- [ ] An open, high-priority task ⏫ 📅 2025-10-25 #project
- [x] A completed task ✅ 2025-10-19 #project
"""
        Path(os.path.join(self.vault_path, "file1.md")).write_text(content1)

        content2 = """
- [ ] An overdue task 📅 2025-10-15 #urgent
- [-] A cancelled task 🔽
"""
        Path(os.path.join(self.vault_path, "file2.md")).write_text(content2)

    def tearDown(self):
        """Clean up the temporary directory after each test."""
        self.temp_dir.cleanup()

    def test_query_tasks_functionality(self):
        """Test the core logic of the query_tasks function."""
        # Test filtering by status
        open_tasks = query_tasks(vault_path=self.vault_path, status='open')
        self.assertEqual(len(open_tasks), 2)
        self.assertIsInstance(open_tasks[0], dict)  # Should return dictionaries

        # Test filtering by priority
        high_priority_tasks = query_tasks(vault_path=self.vault_path, priority='high')
        self.assertEqual(len(high_priority_tasks), 1)
        self.assertEqual(high_priority_tasks[0]['priority'], TaskPriority.HIGH.value)

        # Test filtering by tag
        project_tasks = query_tasks(vault_path=self.vault_path, tag='project')
        self.assertEqual(len(project_tasks), 2)

        # Test filtering for overdue tasks
        overdue_tasks = query_tasks(vault_path=self.vault_path, overdue=True)
        self.assertGreaterEqual(len(overdue_tasks), 1)
        # Should include "An overdue task" (and possibly others depending on current date)
        overdue_descriptions = [t['description'] for t in overdue_tasks]
        self.assertIn("An overdue task", overdue_descriptions)

        # Test combination of filters
        open_project_tasks = query_tasks(vault_path=self.vault_path, status='open', tag='project')
        self.assertEqual(len(open_project_tasks), 1)
        self.assertEqual(open_project_tasks[0]['description'], "An open, high-priority task")

        # Test with no filters (should return all tasks)
        all_tasks = query_tasks(vault_path=self.vault_path)
        self.assertEqual(len(all_tasks), 4)
        
        # Verify all results are dictionaries
        for task in all_tasks:
            self.assertIsInstance(task, dict)
            self.assertIn('description', task)
            self.assertIn('status', task)

if __name__ == "__main__":
    unittest.main()
