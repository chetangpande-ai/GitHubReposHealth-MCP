import asyncio
import logging
import os
import sys
from dotenv import load_dotenv
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain_mcp_adapters.client import MultiServerMCPClient
from .config import Settings


load_dotenv()
DEFAULT_GROQ_MODEL = "openai/gpt-oss-120b"
logger = logging.getLogger("github_health_client")


def looks_like_github_request(prompt: str) -> bool:
    keywords = (
        "commit", "github", "issue", "pull request", "release", "repository",
        "repo", "workflow", "actions", "health", "triage",
    )
    prompt_lower = prompt.lower()
    return any(keyword in prompt_lower for keyword in keywords)


async def _direct_answer(model, prompt: str) -> str:
    logger.info("Invoking LLM directly")
    agent = create_agent(model, [])
    result = await agent.ainvoke({"messages": [{"role": "user", "content": prompt}]})
    logger.info("LLM response received")
    return result["messages"][-1].content


async def run_agent(prompt: str) -> str:
    settings = Settings.from_environment()
    settings.require_groq_api_key()
    model = init_chat_model(f"groq:{settings.groq_model}", temperature=0)
    if not looks_like_github_request(prompt):
        return await _direct_answer(model, prompt)

    owner, repo = settings.require_repository()
    logger.info("Starting MCP server: github_repo_health.mcp_server")
    client = MultiServerMCPClient({
        "github": {
            "transport": "stdio",
            "command": sys.executable,
            "args": ["-m", "github_repo_health.mcp_server"],
        }
    })
    logger.info("Invoking MCP server: list tools")
    tools = await client.get_tools()
    logger.info("MCP server returned tools: %s", ", ".join(tool.name for tool in tools))

    health_uri = f"github://repository/{owner}/{repo}/health"
    logger.info("Invoking MCP server: read resource %s", health_uri)
    health_resources = await client.get_resources("github", uris=health_uri)
    health_context = "\n\n".join(resource.as_string() for resource in health_resources)

    prompt_name = "triage_open_issues" if "triage" in prompt.lower() else "daily_health_report"
    logger.info("Invoking MCP server: get prompt %s", prompt_name)
    workflow_messages = await client.get_prompt(
        "github", prompt_name, arguments={"owner": owner, "repo": repo}
    )
    agent = create_agent(
        model,
        tools,
        system_prompt=(
            "You are a GitHub repository health assistant. Use GitHub MCP tools and "
            "resources to ground every repository claim in live data. Do not invent "
            "issues, commits, or workflow results. State when data is unavailable.\n\n"
            f"Live repository health resource:\n{health_context}"
        ),
    )
    logger.info("Invoking LLM: Groq model=%s", settings.groq_model)
    result = await agent.ainvoke({
        "messages": [*workflow_messages, {"role": "user", "content": prompt}]
    })
    for message in result["messages"]:
        for tool_call in getattr(message, "tool_calls", []):
            logger.info("Invoking MCP tool: %s input=%s", tool_call["name"], tool_call.get("args", {}))
        if message.__class__.__name__ == "ToolMessage":
            logger.info("MCP tool returned: %s", message.name)
    logger.info("LLM response received")
    return result["messages"][-1].content


def main() -> None:
    prompt = " ".join(sys.argv[1:]).strip() or input("Ask a question: ")
    print(asyncio.run(run_agent(prompt)))


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        stream=sys.stderr,
    )
    main()