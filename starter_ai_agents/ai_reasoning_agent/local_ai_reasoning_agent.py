import os

from agno.agent import Agent
from agno.models.google import Gemini
from agno.playground import Playground, serve_playground_app

_api_key = os.environ.get("GOOGLE_API_KEY")
if not _api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY is not set. Create one at https://aistudio.google.com/apikey"
    )

reasoning_agent = Agent(
    name="Reasoning Agent",
    model=Gemini(id="gemini-2.5-flash", api_key=_api_key),
    markdown=True,
)

# UI for Reasoning agent
app = Playground(agents=[reasoning_agent]).get_app()

# Run the Playground app
if __name__ == "__main__":
    serve_playground_app("local_ai_reasoning_agent:app", reload=True)
