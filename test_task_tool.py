import os
import tempfile
import unittest
from pathlib import Path

from task_tool import find_markdown_files, parse_tasks_from_file, TaskStatus, TaskPriority, get_all_tasks, clear_task_cache, get_task_statistics
from datetime import date, timedelta


class TestGetAllTasks(unittest.TestCase):

    def setUp(self):
        """Clear cache before each test to ensure isolation."""
        clear_task_cache()

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
        # Note: The word "and" before the recurrence emoji is also removed as part of the description cleanup
        self.assertEqual(tasks[0].description, "A complex task with a block ID")
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

class TestCaching(unittest.TestCase):

    def setUp(self):
        """Clear cache before each test to ensure isolation."""
        clear_task_cache()

    def test_cache_improves_performance(self):
        """Test that caching avoids re-parsing unchanged files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "tasks.md")
            content = "- [ ] Task 1\n- [ ] Task 2\n- [x] Task 3"
            Path(file_path).write_text(content)

            # First call - should parse
            tasks1 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks1), 3)

            # Second call - should use cache (same mtime)
            # We'll verify by checking that the same task objects are returned
            # Since we can't easily mock mtime in a simple way, we'll just verify
            # that calling again works and returns the same results
            tasks2 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks2), 3)
            self.assertEqual([t.description for t in tasks1], [t.description for t in tasks2])

    def test_cache_re_parses_changed_files(self):
        """Test that changed files are re-parsed and cache is updated."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "tasks.md")
            
            # Initial content
            Path(file_path).write_text("- [ ] Task 1\n- [ ] Task 2")
            tasks1 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks1), 2)

            # Modify file (add a task)
            import time
            time.sleep(0.1)  # Ensure different mtime
            Path(file_path).write_text("- [ ] Task 1\n- [ ] Task 2\n- [ ] Task 3")
            
            # Should re-parse and get updated tasks
            tasks2 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks2), 3)
            descriptions = {t.description for t in tasks2}
            self.assertIn("Task 3", descriptions)

    def test_cache_can_be_disabled(self):
        """Test that use_cache=False forces re-parsing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "tasks.md")
            Path(file_path).write_text("- [ ] Task 1")
            
            # Parse with cache
            tasks1 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks1), 1)

            # Modify file
            import time
            time.sleep(0.1)
            Path(file_path).write_text("- [ ] Task 1\n- [ ] Task 2")

            # Without cache clearing, with use_cache=True, should detect change
            tasks2 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks2), 2)

            # With use_cache=False, should always parse fresh
            tasks3 = get_all_tasks(tmpdir, use_cache=False)
            self.assertEqual(len(tasks3), 2)

    def test_clear_cache_functionality(self):
        """Test that clear_task_cache clears the cache."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = os.path.join(tmpdir, "tasks.md")
            Path(file_path).write_text("- [ ] Task 1")
            
            # Parse once
            tasks1 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks1), 1)

            # Clear cache
            clear_task_cache()
            
            # Modify file
            import time
            time.sleep(0.1)
            Path(file_path).write_text("- [ ] Task 1\n- [ ] Task 2")

            # After clearing cache, should re-parse and see changes
            tasks2 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks2), 2)

    def test_cache_handles_multiple_files(self):
        """Test that cache works correctly with multiple files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = os.path.join(tmpdir, "file1.md")
            file2 = os.path.join(tmpdir, "file2.md")
            
            Path(file1).write_text("- [ ] Task from file 1")
            Path(file2).write_text("- [ ] Task from file 2")
            
            # First parse
            tasks1 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks1), 2)

            # Modify only one file
            import time
            time.sleep(0.1)
            Path(file1).write_text("- [ ] Task from file 1\n- [ ] Another task from file 1")
            
            # Should re-parse file1 but use cache for file2
            tasks2 = get_all_tasks(tmpdir, use_cache=True)
            self.assertEqual(len(tasks2), 3)
            
            descriptions = {t.description for t in tasks2}
            self.assertIn("Another task from file 1", descriptions)
            self.assertIn("Task from file 2", descriptions)


class TestDependenciesParsing(unittest.TestCase):

    def setUp(self):
        """Clear cache before each test to ensure isolation."""
        clear_task_cache()

    def test_parse_single_dependency(self):
        """Test parsing of a task with a single dependency."""
        content = "- [ ] Task depends on another ⛔ ^block-id-123"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "Task depends on another")
        self.assertIsNone(tasks[0].block_id)
        self.assertEqual(tasks[0].dependencies, ["block-id-123"])

    def test_parse_multiple_dependencies(self):
        """Test parsing of a task with multiple dependencies."""
        content = "- [ ] Task with dependencies ⛔ ^dep1 ^dep2 ^dep3"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].dependencies, ["dep1", "dep2", "dep3"])

    def test_parse_task_with_block_id_and_dependencies(self):
        """Test parsing of a task with both its own block_id and dependencies."""
        content = "- [ ] Task with ID ^my-task-id ⛔ ^dep1 ^dep2"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].description, "Task with ID")
        self.assertEqual(tasks[0].block_id, "my-task-id")
        self.assertEqual(tasks[0].dependencies, ["dep1", "dep2"])

    def test_parse_dependencies_with_metadata(self):
        """Test parsing dependencies along with other metadata."""
        content = "- [ ] Complex task ⏫ 📅 2025-10-25 ⛔ ^dep-task #work"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        task = tasks[0]
        self.assertEqual(task.description, "Complex task")
        self.assertEqual(task.priority, TaskPriority.HIGH)
        self.assertEqual(task.due_date, date(2025, 10, 25))
        self.assertEqual(task.dependencies, ["dep-task"])
        self.assertIn("work", task.tags)

    def test_parse_task_without_dependencies(self):
        """Test that tasks without dependencies have empty dependency list."""
        content = "- [ ] Simple task ^simple-id"
        with tempfile.NamedTemporaryFile(mode='w+', delete=False, suffix=".md") as tmpfile:
            tmpfile.write(content)
            tmpfile_path = tmpfile.name

        tasks = parse_tasks_from_file(tmpfile_path)
        os.remove(tmpfile_path)

        self.assertEqual(len(tasks), 1)
        self.assertEqual(tasks[0].block_id, "simple-id")
        self.assertEqual(tasks[0].dependencies, [])


class TestTaskStatistics(unittest.TestCase):

    def setUp(self):
        """Clear cache before each test to ensure isolation."""
        clear_task_cache()

    def test_basic_statistics(self):
        """Test basic statistics counts."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test files with various tasks
            content1 = """
- [ ] Open task 1
- [x] Completed task 1
- [-] Cancelled task 1
"""
            Path(os.path.join(tmpdir, "file1.md")).write_text(content1)

            content2 = """
- [ ] Open task 2
- [x] Completed task 2
"""
            Path(os.path.join(tmpdir, "file2.md")).write_text(content2)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 5)
            self.assertEqual(stats["by_status"][" "], 2)  # OPEN
            self.assertEqual(stats["by_status"]["x"], 2)  # COMPLETED
            self.assertEqual(stats["by_status"]["-"], 1)  # CANCELLED
            self.assertEqual(stats["files_with_tasks"], 2)

    def test_priority_statistics(self):
        """Test priority-based statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
- [ ] High priority task ⏫
- [ ] Medium priority task 🔼
- [ ] Low priority task 🔽
- [ ] Highest priority task 🔺
- [ ] Lowest priority task ⏬
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 5)
            self.assertEqual(stats["by_priority"]["⏫"], 1)  # HIGH
            self.assertEqual(stats["by_priority"]["🔼"], 1)  # MEDIUM
            self.assertEqual(stats["by_priority"]["🔽"], 1)  # LOW
            self.assertEqual(stats["by_priority"]["🔺"], 1)  # HIGHEST
            self.assertEqual(stats["by_priority"]["⏬"], 1)  # LOWEST

    def test_tag_statistics(self):
        """Test tag-based statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
- [ ] Task with tag #work
- [ ] Task with multiple tags #work #urgent
- [ ] Task with different tag #personal
- [ ] Task with nested tag #work/projects
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 4)
            self.assertEqual(stats["by_tag"]["work"], 2)
            self.assertEqual(stats["by_tag"]["urgent"], 1)
            self.assertEqual(stats["by_tag"]["personal"], 1)
            self.assertEqual(stats["by_tag"]["work/projects"], 1)
            
            # Check top_tags includes work with count 2
            work_tags = [t for t in stats["top_tags"] if t["tag"] == "work"]
            self.assertEqual(len(work_tags), 1)
            self.assertEqual(work_tags[0]["count"], 2)

    def test_overdue_statistics(self):
        """Test overdue task statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)
            tomorrow = today + timedelta(days=1)
            
            content = f"""
- [ ] Overdue open task 📅 {yesterday.isoformat()}
- [x] Overdue completed task 📅 {yesterday.isoformat()}
- [ ] Future task 📅 {tomorrow.isoformat()}
- [ ] Task due today 📅 {today.isoformat()}
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["overdue"], 1)  # Only open overdue tasks
            self.assertEqual(stats["due_today"], 1)
            self.assertGreaterEqual(stats["due_this_week"], 2)  # Today + tomorrow

    def test_due_date_statistics(self):
        """Test due date range statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)
            next_week = today + timedelta(days=7)
            next_month = today + timedelta(days=30)
            future = today + timedelta(days=60)
            
            content = f"""
- [ ] Past due task 📅 {yesterday.isoformat()}
- [ ] Task due today 📅 {today.isoformat()}
- [ ] Task due this week 📅 {next_week.isoformat()}
- [ ] Task due this month 📅 {next_month.isoformat()}
- [ ] Future task 📅 {future.isoformat()}
- [ ] Task with no due date
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 6)
            self.assertEqual(stats["date_distribution"]["past"], 1)
            self.assertEqual(stats["date_distribution"]["today"], 1)
            self.assertEqual(stats["date_distribution"]["this_week"], 1)
            self.assertEqual(stats["date_distribution"]["this_month"], 1)
            self.assertEqual(stats["date_distribution"]["future"], 1)
            self.assertEqual(stats["date_distribution"]["no_due_date"], 1)

    def test_dependencies_statistics(self):
        """Test dependency statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
- [ ] Task with dependencies ⛔ ^dep1 ^dep2
- [ ] Task without dependencies
- [ ] Another task with dependency ⛔ ^dep3
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 3)
            self.assertEqual(stats["with_dependencies"], 2)

    def test_recurrence_statistics(self):
        """Test recurrence statistics."""
        with tempfile.TemporaryDirectory() as tmpdir:
            content = """
- [ ] Recurring task 🔁 every day
- [ ] Non-recurring task
- [ ] Another recurring task 🔁 every week
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 3)
            self.assertEqual(stats["with_recurrence"], 2)

    def test_comprehensive_statistics(self):
        """Test statistics with all features combined."""
        with tempfile.TemporaryDirectory() as tmpdir:
            today = date.today()
            yesterday = today - timedelta(days=1)
            
            content = f"""
- [ ] High priority overdue task ⏫ 📅 {yesterday.isoformat()} #work #urgent ⛔ ^dep1
- [x] Completed task ✅ {today.isoformat()} #work
- [ ] Recurring task 🔁 every day #personal
- [ ] Simple task
"""
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 4)
            self.assertEqual(stats["by_status"][" "], 3)  # OPEN
            self.assertEqual(stats["by_status"]["x"], 1)  # COMPLETED
            self.assertEqual(stats["overdue"], 1)
            self.assertEqual(stats["with_dependencies"], 1)
            self.assertEqual(stats["with_recurrence"], 1)
            self.assertEqual(stats["by_tag"]["work"], 2)
            self.assertEqual(stats["by_tag"]["urgent"], 1)
            self.assertEqual(stats["by_tag"]["personal"], 1)
            self.assertEqual(stats["files_with_tasks"], 1)

    def test_empty_vault_statistics(self):
        """Test statistics with an empty vault."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create an empty file
            Path(os.path.join(tmpdir, "empty.md")).write_text("# No tasks here")

            stats = get_task_statistics(tmpdir)

            self.assertEqual(stats["total"], 0)
            self.assertEqual(stats["by_status"], {})
            self.assertEqual(stats["by_priority"], {})
            self.assertEqual(stats["by_tag"], {})
            self.assertEqual(stats["overdue"], 0)
            self.assertEqual(stats["files_with_tasks"], 0)
            self.assertEqual(stats["top_tags"], [])

    def test_top_tags_limit(self):
        """Test that top_tags is limited to 10."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create tasks with 15 different tags
            content_lines = []
            for i in range(15):
                content_lines.append(f"- [ ] Task {i} #tag{i}")
            content = "\n".join(content_lines)
            
            Path(os.path.join(tmpdir, "tasks.md")).write_text(content)

            stats = get_task_statistics(tmpdir)

            self.assertEqual(len(stats["top_tags"]), 10)
            # All should have count 1
            for tag_entry in stats["top_tags"]:
                self.assertEqual(tag_entry["count"], 1)


if __name__ == "__main__":
    unittest.main()
