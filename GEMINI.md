# Project Overview: Task Manager

This project is a Python-based tool for parsing and querying tasks from an Obsidian vault. It is designed to be compatible with the popular "Obsidian Tasks" plugin format.

The tool can be used both as a standalone Command-Line Interface (CLI) and as a server that exposes its functionality as a Managed Component using the FastMCP library.

## Core Components

- **`task_tool.py`**: A CLI for querying tasks. It supports filtering by status, priority, due date, tags, and overdue status.
- **`mcp_server.py`**: A FastMCP server that exposes the task querying functionality. This allows other applications, such as LLMs, to interact with the task data programmatically.
- **`test_task_tool.py` / `test_mcp_server.py`**: Unit tests for the parser and server logic, developed following a TDD approach.
- **`test_vault/`**: A directory containing sample Markdown files with a variety of tasks for manual and automated testing.
- **`test_cli.sh`**: A shell script that runs a comprehensive suite of end-to-end tests against the CLI.

## Building and Running

### Prerequisites

- Python 3.x
- Dependencies from the parent directory's `requirements.txt` file (including `fastmcp`).

### Running the CLI

The `task_tool.py` script provides a powerful CLI for querying your vault.

**Syntax:**
`python3 task_tool.py <path_to_vault> query [FILTERS]`

**Example:**
To find all open, high-priority tasks with the tag `#work` in a vault located at `~/Documents/MyVault`:
```bash
python3 task_tool.py ~/Documents/MyVault query --status open --priority high --tag work
```

### Running the MCP Server

To expose the task query functionality as a service, run the `mcp_server.py` script.

```bash
python3 mcp_server.py
```
This will start a FastMCP server that exposes the `query_tasks` function.

### Running Tests

To verify the functionality of the tool, you can run the automated tests.

- **Unit Tests:** `python3 -m unittest discover`
- **End-to-End CLI Tests:** `./test_cli.sh`
