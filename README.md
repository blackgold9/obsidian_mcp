# Obsidian Tasks MCP Server

Welcome to the Obsidian Tasks MCP Server! This powerful Python-based tool is your ultimate solution for parsing and querying tasks directly from your Obsidian vault. Designed for full compatibility with the "Obsidian Tasks" plugin format, our tool is versatile—use it as a standalone CLI for quick queries or as an MCP (Model Context Protocol) server for integrating with other applications.

## 🚀 Getting Started

Ready to take control of your tasks? Here’s how to get up and running in minutes.

### Prerequisites

- Python 3.12 or higher
- An Obsidian vault filled with your tasks

### Installation

1.  **Clone the Repository**

    ```bash
    git clone https://github.com/your-repo/obsidian-tasks-mcp-server.git
    cd obsidian-tasks-mcp-server
    ```

2.  **Install Dependencies**

    We recommend using `uv` for a fast and reliable installation.

    ```bash
    # Install uv (if you haven't already)
    pip install uv

    # Sync dependencies
    uv sync
    ```

    Alternatively, you can use `pip`.

    ```bash
    pip install -r requirements.txt
    ```

## 💡 Usage

Once you're set up, you can interact with your tasks in two ways:

### 1. Command-Line Interface (CLI)

The `task_tool.py` script provides a comprehensive CLI for querying your tasks.

#### Syntax

```bash
python3 task_tool.py <vault_path> query [OPTIONS]
```

#### Examples

-   **Find all open tasks:**
    ```bash
    python3 task_tool.py ~/Documents/MyVault query --status open
    ```

-   **Find high-priority tasks:**
    ```bash
    python3 task_tool.py ~/Documents/MyVault query --priority high
    ```

-   **Find overdue tasks:**
    ```bash
    python3 task_tool.py ~/Documents/MyVault query --overdue
    ```

-   **Filter by tag:**
    ```bash
    python3 task_tool.py ~/Documents/MyVault query --tag work
    ```

### 2. MCP Server

The `mcp_server.py` script runs a FastMCP server, exposing task-querying functionality as a tool.

#### Starting the Server

You can specify the path to your Obsidian vault using either a command-line argument or an environment variable.

**1. Using the `--vault-path` argument (Recommended):**

```bash
python3 mcp_server.py --vault-path ~/Documents/MyVault
```

**2. Using an Environment Variable:**

```bash
# Set your vault path as an environment variable
export OBSIDIAN_VAULT_PATH=~/Documents/MyVault

# Run the server
python3 mcp_server.py
```

You can also use `uv` to run the server with the argument:
```bash
uv run python3 mcp_server.py --vault-path ~/Documents/MyVault
```

## 👨‍💻 For Developers

Want to contribute or understand the inner workings? Here’s what you need to know.

### Testing

-   **Run all tests:**
    ```bash
    python3 -m unittest discover
    ```

-   **Run end-to-end CLI tests:**
    ```bash
    ./test_cli.sh
    ```

### Project Architecture

-   `task_tool.py`: Core parsing logic and CLI.
-   `mcp_server.py`: MCP server exposing the `query_tasks` tool.
-   `test_*.py`: Unit tests for the parser and server.
-   `test_vault/`: A sample vault for testing.

### Code Style

-   PEP 8 Python style guide
-   Google Style docstrings
-   Type hints

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
