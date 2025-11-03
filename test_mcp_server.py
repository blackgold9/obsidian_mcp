import unittest
import tempfile
import os
from pathlib import Path
from datetime import date, timedelta

# This import will fail until we create mcp_server.py
from mcp_server import query_tasks, parse_date
from task_tool import TaskStatus, TaskPriority, clear_task_cache

class TestMCPServer(unittest.TestCase):

    def setUp(self):
        """Set up a temporary vault with test data before each test."""
        clear_task_cache()
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = self.temp_dir.name
        
        # Create some test files
        content1 = """
- [ ] An open, high-priority task ⏫ 📅 2025-10-25 #project
- [x] A completed task ✅ 2025-10-19 #project
- [ ] Task due tomorrow 📅 2025-12-26
- [ ] Task scheduled next week ⏳ 2026-01-02
"""
        Path(os.path.join(self.vault_path, "file1.md")).write_text(content1)

        content2 = """
- [ ] An overdue task 📅 2025-10-15 #urgent
- [-] A cancelled task 🔽
- [ ] Task due next month 📅 2026-01-15
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
        self.assertEqual(len(all_tasks), 6)  # Updated count with new test tasks
        
        # Verify all results are dictionaries
        for task in all_tasks:
            self.assertIsInstance(task, dict)
            self.assertIn('description', task)
            self.assertIn('status', task)

    def test_date_range_queries(self):
        """Test date range queries (due_after, due_before)."""
        # Test due_after
        tasks_after = query_tasks(vault_path=self.vault_path, due_after="2025-12-25")
        # Should include tasks due on 2025-12-26 and later
        due_dates = [t['due_date'] for t in tasks_after if t['due_date']]
        for due_date_str in due_dates:
            if due_date_str:
                due_date = date.fromisoformat(due_date_str) if isinstance(due_date_str, str) else due_date_str
                self.assertGreaterEqual(due_date, date(2025, 12, 25))
        
        # Test due_before
        tasks_before = query_tasks(vault_path=self.vault_path, due_before="2025-10-20")
        # Should include tasks due on or before 2025-10-20
        due_dates = [t['due_date'] for t in tasks_before if t['due_date']]
        for due_date_str in due_dates:
            if due_date_str:
                due_date = date.fromisoformat(due_date_str) if isinstance(due_date_str, str) else due_date_str
                self.assertLessEqual(due_date, date(2025, 10, 20))
        
        # Test due_after and due_before together (range)
        tasks_range = query_tasks(
            vault_path=self.vault_path,
            due_after="2025-10-20",
            due_before="2025-10-26"
        )
        due_dates = [t['due_date'] for t in tasks_range if t['due_date']]
        for due_date_str in due_dates:
            if due_date_str:
                due_date = date.fromisoformat(due_date_str) if isinstance(due_date_str, str) else due_date_str
                self.assertGreaterEqual(due_date, date(2025, 10, 20))
                self.assertLessEqual(due_date, date(2025, 10, 26))

    def test_scheduled_date_range_queries(self):
        """Test scheduled date range queries."""
        # Test scheduled_after
        tasks = query_tasks(vault_path=self.vault_path, scheduled_after="2026-01-01")
        scheduled_dates = [t['scheduled_date'] for t in tasks if t['scheduled_date']]
        if scheduled_dates:
            for scheduled_date_str in scheduled_dates:
                scheduled_date = date.fromisoformat(scheduled_date_str) if isinstance(scheduled_date_str, str) else scheduled_date_str
                self.assertGreaterEqual(scheduled_date, date(2026, 1, 1))

    def test_relative_date_parsing(self):
        """Test parse_date function with relative dates."""
        today = date.today()
        
        # Test today
        self.assertEqual(parse_date("today"), today)
        
        # Test tomorrow
        self.assertEqual(parse_date("tomorrow"), today + timedelta(days=1))
        
        # Test yesterday
        self.assertEqual(parse_date("yesterday"), today - timedelta(days=1))
        
        # Test next week
        result = parse_date("next week")
        expected = today + timedelta(weeks=1)
        self.assertEqual(result, expected)
        
        # Test last week
        result = parse_date("last week")
        expected = today - timedelta(weeks=1)
        self.assertEqual(result, expected)
        
        # Test relative offsets
        result = parse_date("+7 days")
        self.assertEqual(result, today + timedelta(days=7))
        
        result = parse_date("-2 weeks")
        self.assertEqual(result, today - timedelta(weeks=2))
        
        # Test absolute dates still work
        result = parse_date("2025-10-25")
        self.assertEqual(result, date(2025, 10, 25))
        
        # Test invalid date
        with self.assertRaises(ValueError):
            parse_date("invalid-date")

    def test_query_with_relative_dates(self):
        """Test query_tasks with relative date strings."""
        # Test due_after with relative date
        tasks = query_tasks(vault_path=self.vault_path, due_after="today")
        # Should return tasks due today or later
        due_dates = [t['due_date'] for t in tasks if t['due_date']]
        today = date.today()
        for due_date_str in due_dates:
            if due_date_str:
                due_date = date.fromisoformat(due_date_str) if isinstance(due_date_str, str) else due_date_str
                self.assertGreaterEqual(due_date, today)
        
        # Test due_before with relative date
        tasks = query_tasks(vault_path=self.vault_path, due_before="tomorrow")
        # Should return tasks due tomorrow or earlier
        tomorrow = date.today() + timedelta(days=1)
        due_dates = [t['due_date'] for t in tasks if t['due_date']]
        for due_date_str in due_dates:
            if due_date_str:
                due_date = date.fromisoformat(due_date_str) if isinstance(due_date_str, str) else due_date_str
                self.assertLessEqual(due_date, tomorrow)


if __name__ == "__main__":
    unittest.main()
