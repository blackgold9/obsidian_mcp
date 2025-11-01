from datetime import datetime, date
from typing import List, Optional, Dict, Any

from fastmcp import FastMCP
from fastmcp.tools import FunctionTool

from task_tool import get_all_tasks, Task, TaskStatus, TaskPriority

# Create the MCP server instance
app = FastMCP(name="obsidian-tasks", version="0.1.0")


def query_tasks(
    vault_path: str,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    due: Optional[str] = None,
    overdue: Optional[bool] = False,
    tag: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Queries tasks from an Obsidian vault with optional filters.
    
    Args:
        vault_path: The absolute path to the Obsidian vault directory.
        status: Filter by status: 'open', 'completed', or 'cancelled'.
        priority: Filter by priority: 'highest', 'high', 'medium', 'low', or 'lowest'.
        due: Filter by due date in YYYY-MM-DD format.
        overdue: If True, filter for overdue tasks (open tasks with due date in past).
        tag: Filter by tag (without the # prefix).
    
    Returns:
        A list of task dictionaries with all task properties.
    """
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
            due_date = datetime.strptime(due, "%Y-%m-%d").date()
            filtered_tasks = [t for t in filtered_tasks if t.due_date == due_date]
        except (ValueError, TypeError):
            pass # Ignore invalid date formats

    if overdue:
        today = date.today()
        filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date < today and t.status == TaskStatus.OPEN]

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
