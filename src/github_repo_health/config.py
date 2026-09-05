import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    groq_model: str
    github_owner: str | None
    github_repo: str | None
    github_token: str | None

    @classmethod
    def from_environment(cls) -> "Settings":
        github_token = os.getenv("GITHUB_TOKEN")
        if github_token in {"", "your-github-token", "your_token_here"}:
            github_token = None
        return cls(
            groq_api_key=os.getenv("GROQ_API_KEY"),
            groq_model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
            github_owner=os.getenv("GITHUB_OWNER"),
            github_repo=os.getenv("GITHUB_REPO"),
            github_token=github_token,
        )

    def require_groq_api_key(self) -> str:
        if not self.groq_api_key:
            raise RuntimeError("Set GROQ_API_KEY before running the agent")
        return self.groq_api_key

    def require_repository(self) -> tuple[str, str]:
        if not self.github_owner or not self.github_repo:
            raise RuntimeError(
                "Set GITHUB_OWNER and GITHUB_REPO before asking GitHub questions"
            )
        return self.github_owner, self.github_repo