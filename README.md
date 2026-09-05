# GitHub Repository Health MCP

A real-time GitHub repository health assistant built with the Model Context Protocol, LangChain 1.x, and Groq.

The agent can summarize repository activity, open issues, recent commits, and GitHub Actions workflow health using live GitHub API data.

## Project Structure

```text
MCP-Project1/
├── src/
│   └── github_repo_health/
│       ├── __init__.py       # Package metadata
│       ├── config.py         # Environment-backed settings
│       ├── github_api.py      # GitHub REST client and data shaping
│       ├── mcp_server.py     # MCP tools, resources, and prompts
│       └── agent.py           # LangChain + Groq application client
├── tests/
│   └── test_github_api.py    # Fast unit tests for API helpers
├── .env.example              # Configuration template
├── pyproject.toml            # Dependencies and console entry points
├── uv.lock                   # Reproducible dependency lockfile
└── README.md
```

The separation keeps responsibilities small:

- `github_api.py` knows how to call GitHub.
- `mcp_server.py` exposes GitHub capabilities through MCP.
- `agent.py` decides whether to use MCP or call Groq directly.
- `tests/` verifies pure helper behavior without network calls.

## MCP Capabilities

### Tools

| Tool | Purpose |
| --- | --- |
| `get_repository_info` | Repository metadata, stars, forks, language, branch, and issue count. |
| `get_open_issues` | Current open issues, excluding pull requests. |
| `get_recent_commits` | Recent commit messages, authors, dates, and links. |
| `get_workflow_runs` | Recent GitHub Actions statuses and conclusions. |

### Resources

| Resource | Purpose |
| --- | --- |
| `github://repository/{owner}/{repo}/health` | Live health snapshot combining repository metadata, issues, and workflows. |
| `github://repository/{owner}/{repo}/issues` | Current open issues as JSON. |

### Prompts

| Prompt | Purpose |
| --- | --- |
| `daily_health_report` | Produces a repository health report with risks and recommended actions. |
| `triage_open_issues` | Groups and prioritizes current open issues. |

The first version is read-only. It does not create, modify, close, or label GitHub issues.

## Setup

Install dependencies:

```powershell
uv sync
```

Create local configuration:

```powershell
Copy-Item .env.example .env
```

Set these values in `.env`:

```text
GROQ_API_KEY=your-groq-api-key
GROQ_MODEL=openai/gpt-oss-120b
GITHUB_OWNER=modelcontextprotocol
GITHUB_REPO=python-sdk
GITHUB_TOKEN=your-github-token
```

`GITHUB_TOKEN` is optional for public repositories but recommended for a higher GitHub API rate limit. Never commit `.env`.

## Run The Agent

The installed console command starts the LangChain agent:

```powershell
uv run github-health-agent "Is this repository healthy?"
uv run github-health-agent "What are the most important open issues?"
uv run github-health-agent "Did the latest workflow pass?"
uv run github-health-agent "Prepare a release-readiness report."
```

You can also run it as a module:

```powershell
uv run python -m github_repo_health.agent "Summarize recent activity."
```

To run only the MCP server for an MCP host such as Claude Desktop:

```powershell
uv run github-health-mcp
```

The MCP server is normally started automatically by the LangChain client over stdio.

## Agent Flow

For a repository question:

1. `agent.py` identifies the request as GitHub-related.
2. It starts `github_repo_health.mcp_server` over stdio.
3. The MCP adapter discovers tools and reads the health resource.
4. The client loads `daily_health_report` or `triage_open_issues`.
5. Groq decides which live GitHub tools to call.
6. `github_api.py` calls GitHub and returns shaped data.
7. Groq summarizes the results into the final answer.

For unrelated questions, the agent calls Groq directly without starting the MCP server.

## Logs

Logs go to stderr and the final answer goes to stdout. GitHub requests show entries such as:

```text
Starting MCP server: github_repo_health.mcp_server
Invoking MCP server: list tools
Invoking MCP server: read resource github://repository/owner/repo/health
Invoking MCP server: get prompt daily_health_report
Invoking LLM: Groq model=openai/gpt-oss-120b
Invoking MCP tool: get_workflow_runs input=...
MCP tool returned: get_workflow_runs
LLM response received
```

Direct questions show `Invoking LLM directly` instead.

## Tests

Run the fast local tests:

```powershell
uv run python -m unittest discover -s tests -v
```

The tests do not call GitHub or Groq, so they are safe to run without API keys.