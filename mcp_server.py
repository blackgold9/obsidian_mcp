"""A server for querying tasks from an Obsidian vault.

This module provides a server that exposes the task-querying functionality of
the `task_tool` module as a set of tools that can be called remotely.
"""
import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from task_tool import get_all_tasks, Task, TaskStatus, TaskPriority, get_task_statistics

# Create the MCP server instance
app = FastMCP(name="obsidian-tasks", version="0.1.0")


def parse_date(date_str: str) -> date:
    """Parses a date string into a date object.

    This function supports both absolute dates (YYYY-MM-DD) and relative dates.

    Supported relative dates:
        - 'today', 'tomorrow', 'yesterday'
        - 'next week', 'last week'
        - 'next month', 'last month'
        - 'next year', 'last year'
        - '+N days', '-N days', '+N weeks', '-N weeks' (e.g., '+7 days',
          '-2 weeks')

    Args:
        date_str: The date string to parse.

    Returns:
        A date object.

    Raises:
        ValueError: If the date string cannot be parsed.
    """
    today = date.today()
    date_str_lower = date_str.lower().strip()
    
    # Try relative date strings first
    if date_str_lower == 'today':
        return today
    elif date_str_lower == 'tomorrow':
        return today + timedelta(days=1)
    elif date_str_lower == 'yesterday':
        return today - timedelta(days=1)
    elif date_str_lower == 'next week':
        return today + timedelta(weeks=1)
    elif date_str_lower == 'last week':
        return today - timedelta(weeks=1)
    elif date_str_lower == 'next month':
        # Approximate: add 30 days
        return today + timedelta(days=30)
    elif date_str_lower == 'last month':
        return today - timedelta(days=30)
    elif date_str_lower == 'next year':
        return date(today.year + 1, today.month, today.day)
    elif date_str_lower == 'last year':
        return date(today.year - 1, today.month, today.day)
    elif date_str_lower.startswith('+') or date_str_lower.startswith('-'):
        # Parse relative dates like "+7 days", "-2 weeks"
        parts = date_str_lower.split()
        if len(parts) == 2:
            try:
                offset = int(parts[0])
                unit = parts[1]
                if unit in ('day', 'days'):
                    return today + timedelta(days=offset)
                elif unit in ('week', 'weeks'):
                    return today + timedelta(weeks=offset)
                elif unit in ('month', 'months'):
                    return today + timedelta(days=offset * 30)  # Approximate
                elif unit in ('year', 'years'):
                    return date(today.year + offset, today.month, today.day)
            except ValueError:
                pass
    
    # Try absolute date format (YYYY-MM-DD)
    try:
        return datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Unable to parse date: '{date_str}'. Use YYYY-MM-DD format or relative dates like 'today', 'tomorrow', '+7 days'.")


def query_tasks(
    vault_path: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due: Optional[str] = None,
    overdue: Optional[bool] = False,
    tag: Optional[str] = None,
    due_after: Optional[str] = None,
    due_before: Optional[str] = None,
    scheduled_after: Optional[str] = None,
    scheduled_before: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Queries tasks from an Obsidian vault with optional filters.

    Args:
        vault_path: The absolute path to the Obsidian vault directory. If not
            provided, the `OBSIDIAN_VAULT_PATH` environment variable will be
            used.
        status: A status to filter by. Can be 'open', 'completed', or
            'cancelled'.
        priority: A priority to filter by. Can be 'highest', 'high', 'medium',
            'low', or 'lowest'.
        due: A due date to filter by. Can be in YYYY-MM-DD format or a
            relative date string.
        overdue: If True, only return overdue tasks.
        tag: A tag to filter by.
        due_after: A date to filter tasks due on or after.
        due_before: A date to filter tasks due on or before.
        scheduled_after: A date to filter tasks scheduled on or after.
        scheduled_before: A date to filter tasks scheduled on or before.

    Returns:
        A list of task dictionaries, with each dictionary representing a task.

    Raises:
        ValueError: If `vault_path` is not provided and the
            `OBSIDIAN_VAULT_PATH` environment variable is not set.
    """
    # Get vault path from parameter or environment variable
    if vault_path is None:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if vault_path is None:
            raise ValueError(
                "vault_path must be provided as a parameter or set via OBSIDIAN_VAULT_PATH environment variable"
            )
    
    all_tasks = get_all_tasks(vault_path)
    filtered_tasks = all_tasks

    if status:
        status_map = {
            'open': TaskStatus.OPEN,
            'completed': TaskStatus.COMPLETED,
            'cancelled': TaskStatus.CANCELLED
        }
        filtered_tasks = [t for t in filtered_tasks if t.status == status_map.get(status)]

    if priority:
        priority_map = {
            'highest': TaskPriority.HIGHEST,
            'high': TaskPriority.HIGH,
            'medium': TaskPriority.MEDIUM,
            'low': TaskPriority.LOW,
            'lowest': TaskPriority.LOWEST
        }
        filtered_tasks = [t for t in filtered_tasks if t.priority == priority_map.get(priority)]

    if due:
        try:
            due_date = parse_date(due)
            filtered_tasks = [t for t in filtered_tasks if t.due_date == due_date]
        except ValueError:
            pass # Ignore invalid date formats

    if overdue:
        today = date.today()
        filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date < today and t.status == TaskStatus.OPEN]

    if due_after:
        try:
            after_date = parse_date(due_after)
            filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date >= after_date]
        except ValueError:
            pass # Ignore invalid date formats

    if due_before:
        try:
            before_date = parse_date(due_before)
            filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date <= before_date]
        except ValueError:
            pass # Ignore invalid date formats

    if scheduled_after:
        try:
            after_date = parse_date(scheduled_after)
            filtered_tasks = [t for t in filtered_tasks if t.scheduled_date and t.scheduled_date >= after_date]
        except ValueError:
            pass # Ignore invalid date formats

    if scheduled_before:
        try:
            before_date = parse_date(scheduled_before)
            filtered_tasks = [t for t in filtered_tasks if t.scheduled_date and t.scheduled_date <= before_date]
        except ValueError:
            pass # Ignore invalid date formats

    if tag:
        filtered_tasks = [t for t in filtered_tasks if tag in t.tags]

    # Convert Task objects to dictionaries for JSON serialization
    return [task_to_dict(t) for t in filtered_tasks]


def task_to_dict(task: Task) -> Dict[str, Any]:
    """Converts a Task object to a dictionary for JSON serialization.

    Args:
        task: The Task object to convert.

    Returns:
        A dictionary representation of the task.
    """
    return {
        "description": task.description,
        "status": task.status.value,
        "priority": task.priority.value,
        "created_date": task.created_date.isoformat() if task.created_date else None,
        "start_date": task.start_date.isoformat() if task.start_date else None,
        "scheduled_date": task.scheduled_date.isoformat() if task.scheduled_date else None,
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "done_date": task.done_date.isoformat() if task.done_date else None,
        "cancelled_date": task.cancelled_date.isoformat() if task.cancelled_date else None,
        "recurrence": task.recurrence,
        "block_id": task.block_id,
        "dependencies": task.dependencies,
        "tags": task.tags,
        "file_path": task.file_path,
        "line_number": task.line_number,
        "raw_text": task.raw_text
    }


def get_statistics(vault_path: Optional[str] = None) -> Dict[str, Any]:
    """Gets comprehensive statistics about tasks in the Obsidian vault.

    Args:
        vault_path: The absolute path to the Obsidian vault directory. If not
            provided, the `OBSIDIAN_VAULT_PATH` environment variable will be
            used.

    Returns:
        A dictionary containing task statistics including:
        - total: Total number of tasks
        - by_status: Count of tasks by status (open, completed, cancelled)
        - by_priority: Count of tasks by priority level
        - by_tag: Count of tasks per tag
        - overdue: Number of overdue open tasks
        - due_today: Number of tasks due today
        - due_this_week: Number of tasks due in the next 7 days
        - due_this_month: Number of tasks due in the next 30 days
        - with_dependencies: Number of tasks that have dependencies
        - with_recurrence: Number of tasks with recurrence rules
        - files_with_tasks: Number of files containing tasks
        - top_tags: Top 10 most common tags with counts
        - date_distribution: Tasks due in date ranges (past, today, this_week, this_month, future, no_due_date)

    Raises:
        ValueError: If `vault_path` is not provided and the
            `OBSIDIAN_VAULT_PATH` environment variable is not set.
    """
    # Get vault path from parameter or environment variable
    if vault_path is None:
        vault_path = os.getenv("OBSIDIAN_VAULT_PATH")
        if vault_path is None:
            raise ValueError(
                "vault_path must be provided as a parameter or set via OBSIDIAN_VAULT_PATH environment variable"
            )
    
    return get_task_statistics(vault_path)


# Register the tools with the MCP server
query_tool = FunctionTool.from_function(query_tasks)
app.add_tool(query_tool)

statistics_tool = FunctionTool.from_function(get_statistics)
app.add_tool(statistics_tool)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Obsidian Tasks MCP Server")
    parser.add_argument(
        "--vault-path",
        help="The absolute path to your Obsidian vault. If not provided, the "
        "OBSIDIAN_VAULT_PATH environment variable will be used.",
    )
    args = parser.parse_args()

    if args.vault_path:
        os.environ["OBSIDIAN_VAULT_PATH"] = args.vault_path

    app.run()
