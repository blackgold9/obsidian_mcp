import os
import tempfile
import unittest
from pathlib import Path

from task_tool import find_markdown_files, parse_tasks_from_file, TaskStatus, TaskPriority, get_all_tasks
from datetime import date


class TestGetAllTasks(unittest.TestCase):

    def test_aggregates_tasks_from_multiple_files(self):
        """
        Tests that get_all_tasks finds and parses tasks from multiple
        files in a directory structure.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # File 1
            content1 = "- [ ] Task 1 from file 1\n- [x] Task 2 from file 1"
            Path(os.path.join(tmpdir, "note1.md")).write_text(content1)

            # File 2 in subdir
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            content2 = "- [ ] Task 1 from file 2 📅 2025-01-01"
            Path(os.path.join(subdir, "note2.md")).write_text(content2)

            # File 3 (no tasks)
            Path(os.path.join(tmpdir, "not_tasks.md")).write_text("# No tasks here")
            
            # File 4 (another task)
            content4 = "- [-] A cancelled task"
            Path(os.path.join(tmpdir, "note4.md")).write_text(content4)

            all_tasks = get_all_tasks(tmpdir)

            self.assertEqual(len(all_tasks), 4)
            
            # Check that descriptions are correct to confirm parsing happened
            descriptions = {task.description for task in all_tasks}
            expected_descriptions = {
                "Task 1 from file 1",
                "Task 2 from file 1",
                "Task 1 from file 2",
                "A cancelled task"
            }
            self.assertEqual(descriptions, expected_descriptions)


class TestParseTasksFromFile(unittest.TestCase):

    def test_parse_tasks_with_metadata(self):
        """Tests parsing of tasks with priority and date metadata using reverse-parsing rules."""
        content = """
- [ ] A high priority task ⏫
- [ ] A normal task with a due date 📅 2023-10-26
- [x] A completed low priority task ✅ 2023-10-25 🔽
- [ ] A task with multiple dates at the end ➕ 2023-10-20 📅 2023-10-26
- [ ] This ⏫ is part of the description, not a priority 📅 2024-01-01
- [ ] This is the description ⏫
"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 6)

        # High priority task
        self.assertEqual(tasks[0].description, "A high priority task")
        self.assertEqual(tasks[0].priority, TaskPriority.HIGH)

        # Task with due date
        self.assertEqual(tasks[1].description, "A normal task with a due date")
        self.assertEqual(tasks[1].due_date, date(2023, 10, 26))
        self.assertEqual(tasks[1].priority, TaskPriority.MEDIUM) # Default

        # Completed low priority task (order reversed)
        self.assertEqual(tasks[2].description, "A completed low priority task")
        self.assertEqual(tasks[2].status, TaskStatus.COMPLETED)
        self.assertEqual(tasks[2].priority, TaskPriority.LOW)
        self.assertEqual(tasks[2].done_date, date(2023, 10, 25))

        # Task with multiple dates
        self.assertEqual(tasks[3].description, "A task with multiple dates at the end")
        self.assertEqual(tasks[3].created_date, date(2023, 10, 20))
        self.assertEqual(tasks[3].due_date, date(2023, 10, 26))
        
        # Task with emoji in the middle (should be part of description)
        self.assertEqual(tasks[4].description, "This ⏫ is part of the description, not a priority")
        self.assertEqual(tasks[4].priority, TaskPriority.MEDIUM) # Default
        self.assertEqual(tasks[4].due_date, date(2024, 1, 1))

        # Task with only priority at the end
        self.assertEqual(tasks[5].description, "This is the description")
        self.assertEqual(tasks[5].priority, TaskPriority.HIGH)

    def test_parse_block_id(self):
        """Tests parsing of block IDs."""
        content = "- [ ] A task with a block ID ^my-id"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "A task with a block ID")
        self.assertEqual(tasks[0].block_id, "my-id")

    def test_parse_recurrence(self):
        """Tests parsing of recurrence."""
        content = "- [ ] A recurring task 🔁 every week"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "A recurring task")
        self.assertEqual(tasks[0].recurrence, "every week")

    def test_parse_tags(self):
        """Tests parsing of tags."""
        content = "- [ ] A task with #tags and #more/tags"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "A task with and")
        self.assertEqual(set(tasks[0].tags), {"tags", "more/tags"})

    def test_parse_advanced_metadata(self):
        """Tests parsing of recurrence, block IDs, and tags."""
        content = "- [ ] A complex task with #tags, a block ID ^complex-id, and 🔁 every day"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        # Description should have tags, block ID, and recurrence removed
        # The commas go with the removed tokens, so they shouldn't appear in the description
        self.assertEqual(tasks[0].description, "A complex task with a block ID and")
        self.assertEqual(tasks[0].block_id, "complex-id")
        self.assertEqual(tasks[0].recurrence, "every day")
        self.assertEqual(set(tasks[0].tags), {"tags"})

    def test_parse_basic_tasks(self):
        """Tests parsing of open, completed, and cancelled tasks."""
        content = """
- [ ] An open task.
- [x] A completed task.
- [-] A cancelled task.
This is not a task.
* [ ] Another open task with asterisk.
+ [ ] And one with a plus.
		- [ ] An indented task.
- [?] An invalid status task.
"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 6)

        self.assertEqual(tasks[0].description, "An open task.")
        self.assertEqual(tasks[0].status, TaskStatus.OPEN)
        self.assertEqual(tasks[0].line_number, 2)

        self.assertEqual(tasks[1].description, "A completed task.")
        self.assertEqual(tasks[1].status, TaskStatus.COMPLETED)

        self.assertEqual(tasks[2].description, "A cancelled task.")
        self.assertEqual(tasks[2].status, TaskStatus.CANCELLED)

        self.assertEqual(tasks[3].description, "Another open task with asterisk.")
        self.assertEqual(tasks[3].status, TaskStatus.OPEN)

        self.assertEqual(tasks[4].description, "And one with a plus.")
        self.assertEqual(tasks[4].status, TaskStatus.OPEN)

        self.assertEqual(tasks[5].description, "An indented task.")
        self.assertEqual(tasks[5].status, TaskStatus.OPEN)

    def test_file_with_no_tasks(self):
        """Tests that an empty list is returned for a file with no tasks."""
        content = """
# A Header
This is a regular line of text.
- A list item, but not a task.
"""
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 0)


class TestFindMarkdownFiles(unittest.TestCase):

    def test_find_markdown_files(self):
        """
        Tests that the function correctly finds all .md files recursively
        and ignores other files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a temporary directory structure
            # Root level
            Path(os.path.join(tmpdir, "note1.md")).touch()
            Path(os.path.join(tmpdir, "not_a_note.txt")).touch()

            # Subdirectory
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            Path(os.path.join(subdir, "note2.md")).touch()
            Path(os.path.join(subdir, "image.png")).touch()

            # Deeper subdirectory
            deep_subdir = os.path.join(subdir, "deep")
            os.makedirs(deep_subdir)
            Path(os.path.join(deep_subdir, "note3.md")).touch()

            # Call the function
            found_files = find_markdown_files(tmpdir)

            # Assertions
            self.assertEqual(len(found_files), 3)

            # Use a set for easier comparison, ignoring order
            expected_files = {
                os.path.join(tmpdir, "note1.md"),
                os.path.join(subdir, "note2.md"),
                os.path.join(deep_subdir, "note3.md"),
            }
            self.assertEqual(set(found_files), expected_files)

    def test_empty_directory(self):
        """
        Tests that the function returns an empty list for a directory
        with no markdown files.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            Path(os.path.join(tmpdir, "file.txt")).touch()
            subdir = os.path.join(tmpdir, "subdir")
            os.makedirs(subdir)
            Path(os.path.join(subdir, "another_file.log")).touch()

            found_files = find_markdown_files(tmpdir)
            self.assertEqual(len(found_files), 0)


import sys
from io import StringIO
from unittest.mock import patch

from task_tool import main

class TestMain(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.vault_path = self.temp_dir.name

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_query_command(self):
        """Tests the 'query' command of the main function with proper CLI arguments."""
        # Create some test files with tasks
        content1 = "- [ ] Task 1 📅 2025-10-20\n- [x] Task 2 ✅ 2025-10-19"
        Path(os.path.join(self.vault_path, "note1.md")).write_text(content1)

        content2 = "- [ ] Task 3 ⏫\n- [ ] Task 4 📅 2025-10-20"
        Path(os.path.join(self.vault_path, "note2.md")).write_text(content2)

        # --- Test Case 1: Query for tasks due on specific date ---
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch.object(sys, 'argv', [
                'task_tool.py',
                self.vault_path,
                'query',
                '--due', '2025-10-20'
            ]):
                main()
                output = fake_out.getvalue().strip()
                self.assertIn("Found 2 tasks matching your query.", output)
                self.assertIn("Task 1", output)
                self.assertIn("Task 4", output)

        # --- Test Case 2: Query for completed tasks (verbose) ---
        with patch('sys.stdout', new=StringIO()) as fake_out:
            with patch.object(sys, 'argv', [
                'task_tool.py',
                self.vault_path,
                'query',
                '--status', 'completed',
                '--verbose'
            ]):
                main()
                output = fake_out.getvalue().strip()
                self.assertIn("Found 1 tasks matching your query.", output)
                self.assertIn("- [x] Task 2 ✅ 2025-10-19", output)

if __name__ == "__main__":
    unittest.main()
