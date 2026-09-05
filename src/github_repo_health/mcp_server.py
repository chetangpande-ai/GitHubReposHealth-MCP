import json

from dotenv import load_dotenv
from mcp.server.fastmcp import FastMCP

from .config import Settings
from .github_api import GitHubClient


load_dotenv()
server = FastMCP("GitHub Repository Health")
github = GitHubClient(Settings.from_environment().github_token)


@server.tool()
def get_repository_info(owner: str, repo: str) -> str:
    """Get current metadata and activity counters for a GitHub repository."""
    return json.dumps(github.repository_info(owner, repo), indent=2)


@server.tool()
def get_open_issues(owner: str, repo: str, limit: int = 10) -> str:
    """Get open issues, excluding pull requests, for a GitHub repository."""
    return json.dumps(github.open_issues(owner, repo, limit), indent=2)


@server.tool()
def get_recent_commits(owner: str, repo: str, limit: int = 10) -> str:
    """Get recent commits and their authors for a GitHub repository."""
    return json.dumps(github.recent_commits(owner, repo, limit), indent=2)


@server.tool()
def get_workflow_runs(owner: str, repo: str, limit: int = 10) -> str:
    """Get recent GitHub Actions workflow runs and their conclusions."""
    return json.dumps(github.workflow_runs(owner, repo, limit), indent=2)


@server.resource(
    "github://repository/{owner}/{repo}/health",
    name="repository_health",
    description="Live GitHub repository metadata and health indicators.",
    mime_type="application/json",
)
def repository_health(owner: str, repo: str) -> str:
    """Read a live repository health snapshot as JSON."""
    return json.dumps(github.health_snapshot(owner, repo), indent=2)


@server.resource(
    "github://repository/{owner}/{repo}/issues",
    name="repository_issues",
    description="Current open GitHub issues for a repository.",
    mime_type="application/json",
)
def repository_issues(owner: str, repo: str) -> str:
    """Read the current open issues as JSON."""
    return json.dumps(github.open_issues(owner, repo, 30), indent=2)


@server.prompt(
    name="daily_health_report",
    description="Create a prompt for a current GitHub repository health report.",
)
def daily_health_report(owner: str, repo: str) -> list[dict[str, str]]:
    """Ask an agent to analyze a repository's live health indicators."""
    return [{
        "role": "user",
        "content": (
            f"Prepare a current health report for GitHub repository {owner}/{repo}. "
            "Use the repository health resource and relevant tools. Summarize open "
            "issues, recent activity, workflow reliability, risks, and the top three "
            "recommended next actions."
        ),
    }]


@server.prompt(
    name="triage_open_issues",
    description="Create a prompt for prioritizing a repository's open issues.",
)
def triage_open_issues(owner: str, repo: str) -> list[dict[str, str]]:
    """Ask an agent to prioritize the repository's current open issues."""
    return [{
        "role": "user",
        "content": (
            f"Review and triage the open issues in GitHub repository {owner}/{repo}. "
            "Use the issues resource, group related issues, identify likely bugs or "
            "blockers, and recommend a priority with a short justification."
        ),
    }]


def main() -> None:
    server.run()


if __name__ == "__main__":
    main()