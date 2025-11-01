### 1. Understanding the Goal

The objective is to design a system of Python functions capable of recursively searching an Obsidian vault for tasks written in Markdown. This system must parse and understand the specific metadata format used by the "Obsidian Tasks" plugin (as detailed in `obsisian_format.md`). The end goal is to provide a query interface that allows users to filter tasks based on their status (e.g., open, completed, cancelled), date-based properties (e.g., overdue, due soon), priority, and combinations of these criteria.

### 2. Investigation & Analysis

Before designing the solution, a thorough investigation of the existing environment and task format is necessary.

1.  **Analyze Task Specification:** The first and most critical step is to perform an in-depth review of the `@obsisian_format.md` file. This will provide the ground truth for the task parsing logic.
    *   **Search for:** All emoji indicators (`🔺`, `⏫`, `🔼`, `🔽`, `⏬`, `➕`, `🛫`, `⏳`, `📅`, `✅`, `❌`, `🔁`, `🆔`, `⛔`).
    *   **Read:** The sections on "Basic Tasks" and "Advanced Tasks (Tasks Plugin Format)" to understand the core structure (`- [ ]`, `- [x]`, `[- ]`) and the exact syntax for dates, priorities, and recurrence.
    *   **Questions to Answer:**
        *   Is the order of metadata emojis fixed, or can they appear in any order on the line?
        *   What is the exact date format (assumed to be `YYYY-MM-DD`)?
        *   How are recurrence rules structured? Is parsing them in scope for the initial version?
        *   What are all possible task statuses and their Markdown representations?

2.  **Review Existing Codebase:** Examine the existing Python scripts (`calendar_tool.py`, `doc_tool.py`, `combine.py`) to understand current conventions and identify reusable patterns.
    *   **Search for:** `os.walk`, `re` (regular expressions), `datetime`, and `argparse`. This will show how file system traversal, text parsing, date handling, and command-line interfaces are currently implemented.
    *   **Read:** The file processing loops and argument parsing sections of these files to align the new functionality with the existing architectural style.
    *   **Questions to Answer:**
        *   Is there a preferred library or style for command-line argument parsing? (`argparse` is present).
        *   What is the project's coding style (e.g., naming conventions, function structure)?
        *   Are there any existing utility functions for file I/O or date manipulation that can be reused?

3.  **Examine Dependencies:** Read the `requirements.txt` file to see the project's current dependencies.
    *   **Questions to Answer:**
        *   Are there any libraries that could simplify date parsing or other aspects of the task? (The current list is minimal, suggesting standard libraries will be the primary tools).

### 3. Proposed Strategic Approach

The strategy is divided into three distinct phases, starting with a solid foundation for parsing and progressively building up to a user-facing query tool.

**Phase 1: Core Models & Parsing Engine**

This phase focuses on accurately representing and extracting task information from text.

1.  **Task Data Structure:** Define a Python `dataclass` or `class` named `Task`. This object will be the canonical representation of a task and will have attributes for:
    *   `description` (str)
    *   `status` (Enum: `OPEN`, `COMPLETED`, `CANCELLED`)
    *   `priority` (Enum: `HIGHEST`, `HIGH`, `MEDIUM`, `LOW`, `LOWEST`, `NONE`)
    *   `due_date` (Optional[datetime.date])
    *   `scheduled_date` (Optional[datetime.date])
    *   `done_date` (Optional[datetime.date])
    *   `file_path` (str): The path to the file containing the task.
    *   `line_number` (int): The line number where the task is located.
    *   `raw_text` (str): The original line of text.

2.  **File Discovery:** Implement a function `find_markdown_files(vault_path: str) -> List[str]` that recursively traverses the given directory and returns a list of absolute paths to all `.md` files.

3.  **Task Parser:** Develop a function `parse_tasks_from_file(file_path: str) -> List[Task]`. This function will:
    *   Read the content of the file.
    *   Iterate through each line with its line number.
    *   Use a primary regular expression to identify lines that are valid tasks.
    *   For each valid task line, use secondary, more specific regular expressions to extract the description and all metadata (emojis and dates).
    *   Instantiate and populate a `Task` object for each task found, converting date strings to `datetime.date` objects.

**Phase 2: Query & Filtering Logic**

This phase builds the logic for querying the parsed task data.

1.  **Task Collection:** Create a high-level function `get_all_tasks(vault_path: str) -> List[Task]` that orchestrates the process by calling `find_markdown_files` and then `parse_tasks_from_file` for each file, aggregating the results into a single list of `Task` objects.

2.  **Filtering Engine:** Implement a central query function `query_tasks(tasks: List[Task], **filters) -> List[Task]`. This function will accept a list of tasks and keyword arguments for filtering, such as:
    *   `status: str` (e.g., 'open', 'completed')
    *   `priority: str` (e.g., 'high', 'medium')
    *   `due_before: datetime.date`
    *   `due_after: datetime.date`
    *   `is_overdue: bool`

    The function will iteratively apply the specified filters to the task list. The `is_overdue` filter, for example, would check for tasks where `status` is `OPEN` and `due_date` is in the past.

**Phase 3: Command-Line Interface (CLI)**

This phase exposes the query functionality to the user.

1.  **New Script:** Create a new file, `task_tool.py`, to house the CLI.
2.  **Argument Parsing:** Use the `argparse` library to define command-line arguments that correspond to the filters in the `query_tasks` function (e.g., `--status`, `--priority`, `--overdue`).
3.  **Output Formatting:** Implement a function to format the list of filtered `Task` objects into a human-readable string for printing to the console. The output should be clear and include relevant information like the task description, due date, priority, and source file.

### 4. Verification Strategy

1.  **Unit Testing:** Create a `test_task_tool.py` file.
    *   Write dedicated tests for the task-parsing regex against a comprehensive list of sample task strings, including edge cases (e.g., no metadata, all metadata, different orderings if permissible, tasks with links or tags).
    *   Create a mock directory structure with sample `.md` files containing a variety of tasks.
    *   Write tests for the `query_tasks` function to ensure each filter works correctly in isolation and that combinations of filters produce the expected intersection of results.

2.  **End-to-End Testing:** Execute the `task_tool.py` script from the command line with various argument combinations against the mock vault and manually verify that the console output is correct.

### 5. Anticipated Challenges & Considerations

1.  **Regex Complexity:** Crafting a single, robust regular expression to capture all metadata variations can be complex and hard to maintain. A strategy of using a primary regex to identify a task line, followed by smaller, targeted regexes for each piece of metadata, may be more resilient.
2.  **Performance on Large Vaults:** For vaults with thousands of files, the process of reading and parsing every Markdown file on each query could be slow. The initial implementation will accept this trade-off for simplicity, but a potential future enhancement could involve caching the parsed task list and only re-parsing changed files.
3.  **Scope of Recurrence:** Parsing recurrence rules (e.g., `🔁 every week`) is a significantly complex problem that involves natural language processing. This strategic plan explicitly defers the *interpretation* of these rules. The parser should capture the recurrence rule as a string, but the initial query engine will not calculate future task instances.
4.  **Date and Timezone Handling:** The plan assumes all dates are timezone-naive. This is a reasonable starting point, but if time-of-day or timezone information becomes relevant, the `datetime` handling will need to be made more sophisticated.