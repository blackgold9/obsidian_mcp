"""
A command-line tool for querying and managing tasks in an Obsidian vault.
"""
import argparse
import os
import re
from dataclasses import dataclass, field
from datetime import date, datetime
from enum import Enum
from typing import List, Optional


class TaskStatus(Enum):
    """Represents the status of a task."""
    OPEN = " "
    COMPLETED = "x"
    CANCELLED = "-"


class TaskPriority(Enum):
    """Represents the priority of a task, mapping emoji to a value."""
    HIGHEST = "🔺"
    HIGH = "⏫"
    MEDIUM = "🔼"
    LOW = "🔽"
    LOWEST = "⏬"


@dataclass
class Task:
    """Represents a single task parsed from a Markdown file."""
    description: str
    status: TaskStatus
    priority: TaskPriority = TaskPriority.MEDIUM
    created_date: Optional[date] = None
    start_date: Optional[date] = None
    scheduled_date: Optional[date] = None
    due_date: Optional[date] = None
    done_date: Optional[date] = None
    cancelled_date: Optional[date] = None
    recurrence: Optional[str] = None
    block_id: Optional[str] = None
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    raw_text: str = ""


def find_markdown_files(vault_path: str) -> List[str]:
    """
    Recursively finds all Markdown files in a directory.

    Args:
        vault_path: The absolute path to the Obsidian vault.

    Returns:
        A list of absolute paths to all .md files.
    """
    markdown_files = []
    for root, _, files in os.walk(vault_path):
        for file in files:
            if file.endswith(".md"):
                markdown_files.append(os.path.join(root, file))
    return markdown_files


def parse_tasks_from_file(file_path: str) -> List[Task]:
    """
    Parses tasks from a single Markdown file, including metadata,
    following the Obsidian Tasks plugin's reverse-parsing rules.

    According to the Obsidian Tasks plugin documentation:
    https://publish.obsidian.md/tasks/Support+and+Help/Known+Limitations
    Tasks reads task lines backwards for dates, priorities, and recurrence rules.

    Current implementation:
    - Tags and block IDs: Forward pass (can appear anywhere in description)
    - Dates, priorities, recurrence: Reverse pass (appear at end of task line)

    Args:
        file_path: The absolute path to the Markdown file.

    Returns:
        A list of Task objects found in the file.
    """
    tasks = []
    task_regex = re.compile(r"^\s*[-*+]\s+\[(.)\]\s+(.*)")

    # Regex patterns for metadata components
    priority_regex = re.compile(r"^[🔺⏫🔼🔽⏬]$")
    # Tags may have trailing punctuation (commas, periods, etc.)
    tag_regex = re.compile(r"^#([a-zA-Z0-9_/.-]+)[,.]?$")
    # Block IDs may have trailing punctuation
    block_id_regex = re.compile(r"^\^([a-zA-Z0-9-]+)[,.]?$")
    recurrence_regex = re.compile(r"^🔁$")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                match = task_regex.match(line)
                if not match:
                    continue

                status_char, description = match.groups()

                try:
                    status = TaskStatus(status_char)
                except ValueError:
                    continue

                task = Task(
                    description=description.strip(),
                    status=status,
                    file_path=file_path,
                    line_number=i + 1,
                    raw_text=line.strip()
                )

                tokens = task.description.split()
                
                # First pass: Extract tags, block IDs, and locate recurrence emoji
                # Tags and block IDs can appear anywhere
                # Recurrence emoji location needed for reverse parsing
                tag_indices = set()
                recurrence_emoji_idx = None
                
                for idx, token in enumerate(tokens):
                    tag_match = tag_regex.match(token)
                    if tag_match:
                        task.tags.append(tag_match.group(1))
                        tag_indices.add(idx)
                    
                    # Block IDs can appear anywhere (not just at end)
                    block_id_match = block_id_regex.match(token)
                    if block_id_match:
                        task.block_id = block_id_match.group(1)
                        tag_indices.add(idx)
                    
                    # Locate recurrence emoji (for reverse parsing - will process in pass 2)
                    # NOTE: Current implementation finds recurrence anywhere in forward pass,
                    # but official plugin only recognizes it during backwards parsing from end.
                    # This means recurrence in middle of description may be incorrectly recognized.
                    # Post-MVP: Consider moving to strict reverse-only parsing to match plugin exactly.
                    if recurrence_regex.match(token):
                        recurrence_emoji_idx = idx
                
                # Second pass: Reverse parsing for end-of-line metadata
                # (dates, priorities, recurrence rules)
                # According to Obsidian Tasks plugin: reads backwards for dates, priorities, and recurrence
                # https://publish.obsidian.md/tasks/Support+and+Help/Known+Limitations
                # Only process tokens that aren't tags or block IDs
                unparsed_token_index = len(tokens)
                
                # Process recurrence if emoji was found (post-MVP)
                if recurrence_emoji_idx is not None:
                    # Collect all tokens after the recurrence emoji as recurrence text
                    recurrence_tokens = []
                    j = recurrence_emoji_idx + 1
                    while j < len(tokens):
                        if j not in tag_indices:
                            recurrence_tokens.append(tokens[j])
                            tag_indices.add(j)  # Mark for exclusion
                        j += 1
                    tag_indices.add(recurrence_emoji_idx)  # Mark emoji for exclusion
                    if recurrence_tokens:
                        task.recurrence = " ".join(recurrence_tokens)
                    # Update unparsed_token_index to exclude recurrence
                    unparsed_token_index = recurrence_emoji_idx
                
                # Reverse parsing for dates and priorities
                i = unparsed_token_index - 1
                while i >= 0:
                    # Skip tags, block IDs, and recurrence - they're already processed
                    if i in tag_indices:
                        i -= 1
                        continue
                    
                    token = tokens[i]
                    token_matched = False

                    # 1. Check for Dates (emoji + YYYY-MM-DD)
                    if i > 0 and (i - 1) not in tag_indices:
                        try:
                            parsed_date = datetime.strptime(token, "%Y-%m-%d").date()
                            emoji = tokens[i-1]
                            if emoji in "📅✅➕🛫⏳❌":
                                if emoji == '📅': task.due_date = parsed_date
                                elif emoji == '✅': task.done_date = parsed_date
                                elif emoji == '➕': task.created_date = parsed_date
                                elif emoji == '🛫': task.start_date = parsed_date
                                elif emoji == '⏳': task.scheduled_date = parsed_date
                                elif emoji == '❌': task.cancelled_date = parsed_date
                                unparsed_token_index = i - 1
                                i -= 1 # Consume emoji as well
                                token_matched = True
                        except ValueError:
                            pass # Not a date

                    if token_matched:
                        i -= 1
                        continue

                    # 2. Check for Priority
                    if priority_regex.match(token):
                        try:
                            task.priority = TaskPriority(token)
                            unparsed_token_index = i
                            token_matched = True
                        except ValueError:
                            pass # Not a valid priority

                    if token_matched:
                        i -= 1
                        continue

                    # If no metadata matched, break the loop
                    if not token_matched:
                        break
                    
                    i -= 1

                # Build description excluding tags, recurrence, and end-of-line metadata
                description_tokens = []
                for idx, token in enumerate(tokens[:unparsed_token_index]):
                    if idx not in tag_indices:
                        description_tokens.append(token)
                
                task.description = " ".join(description_tokens)
                tasks.append(task)

    except Exception as e:
        print(f"Error reading or parsing file {file_path}: {e}")

    return tasks


def get_all_tasks(vault_path: str) -> List[Task]:


    """


    Finds and parses all tasks from all Markdown files in a vault.





    Args:


        vault_path: The absolute path to the Obsidian vault.





    Returns:


        A list of all Task objects found in the vault.


    """


    all_tasks = []


    markdown_files = find_markdown_files(vault_path)


    for file_path in markdown_files:


        all_tasks.extend(parse_tasks_from_file(file_path))


    return all_tasks








def main():








    """








    Command-line interface for querying tasks in an Obsidian vault.








    """








    parser = argparse.ArgumentParser(description="Query tasks in an Obsidian vault.")








    parser.add_argument("vault_path", help="The absolute path to your Obsidian vault.")

















    subparsers = parser.add_subparsers(dest="command", required=True)

















    # --- Query Command ---








    query_parser = subparsers.add_parser("query", help="Query tasks based on criteria.")








    query_parser.add_argument("--status", choices=['open', 'completed', 'cancelled'], help="Filter by task status.")








    query_parser.add_argument("--priority", choices=['highest', 'high', 'medium', 'low', 'lowest'], help="Filter by task priority.")








    query_parser.add_argument("--due", help="Filter by due date (YYYY-MM-DD).")








    query_parser.add_argument("--overdue", action="store_true", help="Filter for overdue tasks.")








    query_parser.add_argument("--tag", action="append", help="Filter by tag. Can be specified multiple times.")








    query_parser.add_argument(








        "-v", "--verbose",








        action="store_true",








        help="Print the full raw text of the tasks that match."








    )

















    args = parser.parse_args()

















    if args.command == "query":








        all_tasks = get_all_tasks(args.vault_path)








        filtered_tasks = all_tasks

















        if args.status:








            status_map = {








                'open': TaskStatus.OPEN,








                'completed': TaskStatus.COMPLETED,








                'cancelled': TaskStatus.CANCELLED








            }








            filtered_tasks = [t for t in filtered_tasks if t.status == status_map[args.status]]

















        if args.priority:








            priority_map = {








                'highest': TaskPriority.HIGHEST,








                'high': TaskPriority.HIGH,








                'medium': TaskPriority.MEDIUM,








                'low': TaskPriority.LOW,








                'lowest': TaskPriority.LOWEST








            }








            filtered_tasks = [t for t in filtered_tasks if t.priority == priority_map[args.priority]]

















        if args.due:








            try:








                due_date = datetime.strptime(args.due, "%Y-%m-%d").date()








                filtered_tasks = [t for t in filtered_tasks if t.due_date == due_date]








            except ValueError:








                print(f"Error: Invalid date format for --due. Please use YYYY-MM-DD.")








                return

















        if args.overdue:








            today = date.today()








            filtered_tasks = [t for t in filtered_tasks if t.due_date and t.due_date < today and t.status == TaskStatus.OPEN]

















        if args.tag:








            for tag in args.tag:








                filtered_tasks = [t for t in filtered_tasks if tag in t.tags]

















        print(f"Found {len(filtered_tasks)} tasks matching your query.")








        for task in filtered_tasks:








            if args.verbose:








                print(f"- {task.raw_text} (in {task.file_path})")








            else:








                print(f"- {task.description}")








if __name__ == "__main__":


    main()

