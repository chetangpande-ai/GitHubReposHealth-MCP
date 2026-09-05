import json
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


GITHUB_API_URL = "https://api.github.com"
GITHUB_API_VERSION = "2022-11-28"
DEFAULT_LIMIT = 10
MAX_LIMIT = 30


def validate_limit(limit: int) -> int:
    if not 1 <= limit <= MAX_LIMIT:
        raise ValueError(f"limit must be between 1 and {MAX_LIMIT}")
    return limit


def repository_path(owner: str, repo: str) -> str:
    if not owner.strip() or not repo.strip():
        raise ValueError("owner and repo are required")
    return f"/repos/{owner.strip()}/{repo.strip()}"


class GitHubClient:
    def __init__(self, token: str | None = None):
        self.token = token

    def request(self, path: str, params: dict[str, str | int] | None = None) -> object:
        query = f"?{urlencode(params)}" if params else ""
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-repo-health-mcp",
            "X-GitHub-Api-Version": GITHUB_API_VERSION,
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        request = Request(f"{GITHUB_API_URL}{path}{query}", headers=headers)
        try:
            with urlopen(request, timeout=20) as response:
                return json.load(response)
        except HTTPError as error:
            if error.code == 403:
                raise ValueError(
                    "GitHub API rate limit reached. Set GITHUB_TOKEN for a higher limit."
                ) from error
            if error.code == 404:
                raise ValueError("GitHub repository or endpoint was not found") from error
            raise ValueError(f"GitHub API request failed with HTTP {error.code}") from error
        except URLError as error:
            raise ValueError(f"Could not reach GitHub: {error.reason}") from error

    def repository_info(self, owner: str, repo: str) -> dict[str, object]:
        repository = self.request(repository_path(owner, repo))
        return {
            "full_name": repository.get("full_name"),
            "description": repository.get("description"),
            "visibility": repository.get("visibility"),
            "default_branch": repository.get("default_branch"),
            "stars": repository.get("stargazers_count"),
            "forks": repository.get("forks_count"),
            "open_issues": repository.get("open_issues_count"),
            "language": repository.get("language"),
            "license": (repository.get("license") or {}).get("spdx_id"),
            "updated_at": repository.get("updated_at"),
            "html_url": repository.get("html_url"),
        }

    def open_issues(self, owner: str, repo: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
        issues = self.request(
            f"{repository_path(owner, repo)}/issues",
            {"state": "open", "per_page": validate_limit(limit), "sort": "updated"},
        )
        return [
            {
                "number": issue.get("number"),
                "title": issue.get("title"),
                "labels": [label.get("name") for label in issue.get("labels", [])],
                "user": (issue.get("user") or {}).get("login"),
                "updated_at": issue.get("updated_at"),
                "url": issue.get("html_url"),
            }
            for issue in issues
            if "pull_request" not in issue
        ]

    def recent_commits(self, owner: str, repo: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
        commits = self.request(
            f"{repository_path(owner, repo)}/commits",
            {"per_page": validate_limit(limit)},
        )
        return [
            {
                "sha": commit.get("sha", "")[:7],
                "message": (commit.get("commit") or {}).get("message", "").splitlines()[0],
                "author": ((commit.get("commit") or {}).get("author") or {}).get("name"),
                "date": ((commit.get("commit") or {}).get("author") or {}).get("date"),
                "url": commit.get("html_url"),
            }
            for commit in commits
        ]

    def workflow_runs(self, owner: str, repo: str, limit: int = DEFAULT_LIMIT) -> list[dict]:
        response = self.request(
            f"{repository_path(owner, repo)}/actions/runs",
            {"per_page": validate_limit(limit)},
        )
        return [
            {
                "name": run.get("name"),
                "status": run.get("status"),
                "conclusion": run.get("conclusion"),
                "branch": run.get("head_branch"),
                "event": run.get("event"),
                "created_at": run.get("created_at"),
                "updated_at": run.get("updated_at"),
                "url": run.get("html_url"),
            }
            for run in response.get("workflow_runs", [])
        ]

    def health_snapshot(self, owner: str, repo: str) -> dict[str, object]:
        repository = self.repository_info(owner, repo)
        issues = self.open_issues(owner, repo)
        workflows = self.workflow_runs(owner, repo)
        completed = [run for run in workflows if run.get("conclusion")]
        failed = [run for run in completed if run.get("conclusion") != "success"]
        return {
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "repository": repository,
            "indicators": {
                "open_issue_count_returned": len(issues),
                "workflow_runs_checked": len(workflows),
                "completed_workflows_failed": len(failed),
                "latest_workflow": workflows[0] if workflows else None,
            },
        }