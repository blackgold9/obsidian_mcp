import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from task_tool import get_all_tasks, Task, TaskStatus, TaskPriority

# Create the MCP server instance
app = FastMCP(name="obsidian-tasks", version="0.1.0")


def parse_date(date_str: str) -> date:
    """
    Parse a date string, supporting both absolute dates (YYYY-MM-DD) and relative dates.
    
    Supported relative dates:
    - 'today', 'tomorrow', 'yesterday'
    - 'next week', 'last week'
    - 'next month', 'last month'
    - 'next year', 'last year'
    - '+N days', '-N days', '+N weeks', '-N weeks' (e.g., '+7 days', '-2 weeks')
    
    Args:
        date_str: Date string to parse
        
    Returns:
        A date object
        
    Raises:
        ValueError: If date string cannot be parsed
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
    """
    Queries tasks from an Obsidian vault with optional filters.
    
    Args:
        vault_path: The absolute path to the Obsidian vault directory. If not provided, 
                   will use the OBSIDIAN_VAULT_PATH environment variable.
        status: Filter by status: 'open', 'completed', or 'cancelled'.
        priority: Filter by priority: 'highest', 'high', 'medium', 'low', or 'lowest'.
        due: Filter by exact due date. Supports YYYY-MM-DD format or relative dates.
        overdue: If True, filter for overdue tasks (open tasks with due date in past).
        tag: Filter by tag (without the # prefix).
        due_after: Filter tasks with due date on or after this date. Supports relative dates.
        due_before: Filter tasks with due date on or before this date. Supports relative dates.
        scheduled_after: Filter tasks with scheduled date on or after this date. Supports relative dates.
        scheduled_before: Filter tasks with scheduled date on or before this date. Supports relative dates.
    
    Returns:
        A list of task dictionaries with all task properties.
    
    Raises:
        ValueError: If vault_path is not provided and OBSIDIAN_VAULT_PATH is not set, 
                   or if date strings cannot be parsed.
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
    """
    Convert a Task object to a dictionary for JSON serialization.
    
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


# Register the tool with the MCP server
tool = FunctionTool.from_function(query_tasks)
app.add_tool(tool)


if __name__ == "__main__":
    app.run()
