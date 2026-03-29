import os

from agno.agent import Agent
from agno.models.google import Gemini
from rich.console import Console

_api_key = os.environ.get("GOOGLE_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Create one at https://aistudio.google.com/apikey"
    )

regular_agent = Agent(
    model=Gemini(id="gemini-2.5-flash", api_key=_api_key),
    markdown=True,
)
console = Console()
reasoning_agent = Agent(
    model=Gemini(id="gemini-2.5-pro", api_key=_api_key),
    reasoning=True,
    markdown=True,
    structured_outputs=True,
)

task = "How many 'r' are in the word 'supercalifragilisticexpialidocious'?"

console.rule("[bold green]Regular Agent[/bold green]")
regular_agent.print_response(task, stream=True)
console.rule("[bold yellow]Reasoning Agent[/bold yellow]")
reasoning_agent.print_response(task, stream=True, show_full_reasoning=True)
