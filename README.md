# Obsidian Tasks MCP Server

A Python-based tool for parsing and querying tasks from an Obsidian vault. Compatible with the "Obsidian Tasks" plugin format, this tool can be used as both a standalone CLI and as an MCP (Model Context Protocol) server.

## Features

- ✅ Parse tasks from Markdown files following Obsidian Tasks format
- ✅ Query tasks with filters: status, priority, due date, tags, overdue
- ✅ Support for task metadata: dates, priorities, recurrence, dependencies, block IDs
- ✅ **Caching system** - Only re-parses changed files for improved performance
- ✅ **Dependencies parsing** - Parses task dependencies using `⛔` emoji and block ID references
- 🚧 Date range queries (coming soon)
- 🚧 Structured logging (coming soon)

## Installation

### Prerequisites

- Python 3.12 or higher
- An Obsidian vault with tasks in Markdown files

### Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

## Usage

### Command-Line Interface (CLI)

The `task_tool.py` script provides a CLI for querying tasks.

#### Basic Syntax

```bash
python3 task_tool.py <vault_path> query [OPTIONS]
```

#### Examples

Find all open tasks:
```bash
python3 task_tool.py ~/Documents/MyVault query --status open
```

Find high-priority tasks:
```bash
python3 task_tool.py ~/Documents/MyVault query --priority high
```

Find overdue tasks:
```bash
python3 task_tool.py ~/Documents/MyVault query --overdue
```

Find tasks with a specific tag:
```bash
python3 task_tool.py ~/Documents/MyVault query --tag work
```

Find tasks due on a specific date:
```bash
python3 task_tool.py ~/Documents/MyVault query --due 2025-10-25
```

Combine multiple filters:
```bash
python3 task_tool.py ~/Documents/MyVault query --status open --priority high --tag project
```

Verbose output (shows raw task text):
```bash
python3 task_tool.py ~/Documents/MyVault query --status open --verbose
```

#### Filter Options

- `--status`: Filter by status (`open`, `completed`, `cancelled`)
- `--priority`: Filter by priority (`highest`, `high`, `medium`, `low`, `lowest`)
- `--due`: Filter by due date (format: `YYYY-MM-DD`)
- `--overdue`: Filter for overdue tasks (open tasks with due date in past)
- `--tag`: Filter by tag (without `#` prefix; can be specified multiple times)
- `--verbose` / `-v`: Show full raw text of matching tasks

### MCP Server

The `mcp_server.py` script runs a FastMCP server that exposes task querying functionality.

#### Start the Server

```bash
python3 mcp_server.py
```

Or using uv:

```bash
uv run fastmcp run mcp_server.py
```

#### Environment Variable

The vault path can be set via environment variable to avoid passing it each time:

```bash
export OBSIDIAN_VAULT_PATH=~/Documents/MyVault
python3 mcp_server.py
```

#### MCP Tool: `query_tasks`

The server exposes a `query_tasks` tool with the following parameters:

- `vault_path` (optional): Absolute path to Obsidian vault. If not provided, uses `OBSIDIAN_VAULT_PATH` env var.
- `status` (optional): Filter by status: `'open'`, `'completed'`, or `'cancelled'`
- `priority` (optional): Filter by priority: `'highest'`, `'high'`, `'medium'`, `'low'`, or `'lowest'`
- `due` (optional): Filter by due date in `YYYY-MM-DD` format
- `overdue` (optional): If `True`, filter for overdue tasks
- `tag` (optional): Filter by tag (without `#` prefix)

**Returns:** A list of task dictionaries with all task properties.

## Task Format

The tool parses tasks following the Obsidian Tasks plugin format:

### Basic Task Format

```markdown
- [ ] An open task
- [x] A completed task
- [-] A cancelled task
```

### Task Metadata

Tasks support various metadata elements:

#### Priority

```markdown
- [ ] High priority task ⏫
- [ ] Medium priority task 🔼
- [ ] Low priority task 🔽
```

Priority levels:
- 🔺 Highest
- ⏫ High
- 🔼 Medium (default)
- 🔽 Low
- ⏬ Lowest

#### Dates

```markdown
- [ ] Task due tomorrow 📅 2025-10-26
- [ ] Task starts 🛫 2025-10-25
- [ ] Task scheduled ⏳ 2025-10-27
- [ ] Task created ➕ 2025-10-24
```

Date emojis:
- 📅 Due date
- 🛫 Start date
- ⏳ Scheduled date
- ➕ Created date
- ✅ Done date
- ❌ Cancelled date

#### Tags

```markdown
- [ ] Task with tag #work
- [ ] Task with nested tag #work/projects
```

#### Block IDs

```markdown
- [ ] Task with block ID ^task-123
```

Block IDs can be used to reference tasks.

#### Dependencies

```markdown
- [ ] Task depends on another ⛔ ^block-id-123
- [ ] Task with own ID ^my-id ⛔ ^dep1 ^dep2
```

Tasks can depend on other tasks using the `⛔` emoji followed by block IDs. All block IDs after `⛔` are dependencies.

#### Recurrence

```markdown
- [ ] Daily task 🔁 every day
- [ ] Weekly task 🔁 every week on Monday
```

#### Combined Example

```markdown
- [ ] Complete project proposal ⏫ 📅 2025-10-30 #work/projects ^proposal-task
- [ ] Review proposal ⛔ ^proposal-task 📅 2025-11-01 #work/review
```

## Architecture

### Core Components

- **`task_tool.py`**: CLI interface and core parsing logic
  - `Task` dataclass: Represents a parsed task
  - `parse_tasks_from_file()`: Parses tasks from a Markdown file
  - `get_all_tasks()`: Collects all tasks from a vault with caching
  - `find_markdown_files()`: Recursively finds all `.md` files

- **`mcp_server.py`**: FastMCP server exposing query functionality
  - `query_tasks()`: Main query function exposed as MCP tool
  - `task_to_dict()`: Converts Task objects to JSON-serializable dictionaries

### Caching

The tool uses a file modification time-based cache to improve performance:

- Files are parsed on first access
- Cache entries include modification time and parsed tasks
- Files are only re-parsed if their modification time changes
- Cache can be cleared with `clear_task_cache()` function

### Parsing Strategy

Tasks are parsed following Obsidian Tasks plugin rules:

1. **Forward pass**: Extracts tags and locates emojis (recurrence, dependencies)
2. **Reverse pass**: Extracts dates, priorities, and recurrence rules from the end of the task line
3. **Block IDs**: Processed based on context (before `⛔` = task's own ID, after `⛔` = dependencies)

## Testing

### Run All Tests

```bash
python3 -m unittest discover
```

### Run Specific Test Suite

```bash
# CLI tests
python3 -m unittest test_task_tool

# MCP server tests
python3 -m unittest test_mcp_server
```

### End-to-End CLI Tests

```bash
./test_cli.sh
```

## Project Structure

```
obsidian_mcp/
├── task_tool.py          # Core parsing and CLI
├── mcp_server.py          # MCP server
├── test_task_tool.py      # Unit tests for parsing
├── test_mcp_server.py     # Unit tests for MCP server
├── test_cli.sh            # End-to-end CLI tests
├── test_vault/            # Sample vault for testing
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration
└── README.md             # This file
```

## Development

### Code Style

- Follows PEP 8 Python style guide
- Uses type hints where applicable
- Docstrings for all public functions

### Adding New Features

1. Write tests first (TDD approach)
2. Implement feature in `task_tool.py`
3. Add corresponding MCP tool in `mcp_server.py` if needed
4. Update documentation
5. Run tests to verify

## Limitations

- Recurrence rules are captured as strings but not interpreted
- Dependencies are parsed but dependency resolution is not implemented
- Large vaults may take time on first parse (subsequent queries use cache)

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

