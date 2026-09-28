import json
import pathlib

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.apps import App
from google.adk.code_executors import AgentEngineSandboxCodeExecutor
from google.adk.memory import VertexAiMemoryBankService
from google.adk.models import Gemini
from google.adk.tools.preload_memory_tool import PreloadMemoryTool
from google.genai import types

from app.a2ui_utils import a2ui_callback
from app.tools import (
    calculate_fitness_metrics,
    generate_workout_image,
    generate_workout_video,
    get_exercise_details,
    get_workout_history,
    log_workout,
    search_exercise_catalog,
    search_wger_exercises,
)

# Hardcoded project ID & location
PROJECT_ID = "qwiklabs-gcp-02-b47f165a173c"
LOCATION = "us-east1"

# Load Agent Engine resource name from deployment_metadata.json if present
agent_engine_resource_name = None
memory_bank_id = "6292221371762081792"
metadata_path = pathlib.Path(__file__).parent.parent / "deployment_metadata.json"
if metadata_path.exists():
    try:
        with open(metadata_path, "r") as f:
            metadata = json.load(f)
            agent_engine_resource_name = metadata.get("remote_agent_runtime_id")
            if agent_engine_resource_name:
                memory_bank_id = agent_engine_resource_name.split("/")[-1]
    except Exception:
        pass

code_executor = AgentEngineSandboxCodeExecutor(
    agent_engine_resource_name=agent_engine_resource_name
)


# WRITE: after each turn, send the session to Memory Bank for long-term fact extraction
async def generate_memories_callback(callback_context: CallbackContext):
    await callback_context.add_session_to_memory()
    return None


# Memory Bank service builder for cloud deployment
def memory_bank_service_builder():
    return VertexAiMemoryBankService(
        project=PROJECT_ID,
        location=LOCATION,
        agent_engine_id=memory_bank_id,
    )


# Build A2UI System Prompt using v0.8 and BasicCatalog
schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description="You are FitCoach AI, an expert fitness coach and workout strategist.",
    workflow_description=(
        "Help users discover exercise routines, inspect detailed exercise guides, "
        "search live public exercise databases (using Wger API), "
        "calculate fitness metrics (like 1RM, heart rate zones, and BMR/TDEE), "
        "generate visual workout/exercise form guides, "
        "log completed workouts, and view workout history. "
        "Analyze the request and return structured UI when appropriate."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        '{"Image": {"url": {"literalString": "https://..."}}}. Never point an '
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property (\'h1\', \'h2\', \'body\') for "
        "headings and emphasis. "
        "CRITICAL MEMORY DIRECTIVE: Pay special attention to and remember all user allergies, "
        "dietary restrictions, food sensitivities, injuries, and health constraints across sessions using Memory Bank. "
        "Always check and respect the user\'s remembered allergies and dietary restrictions before recommending any meal plans, "
        "nutrition strategies, post-workout snacks, or supplements. "
        "Always use your tools when calculations, exercise lookups, image generation, or logging are requested. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or \'kind\'/\'data\'/\'metadata\' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model="gemini-flash-latest",
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    code_executor=code_executor,
    tools=[
        search_exercise_catalog,
        get_exercise_details,
        log_workout,
        get_workout_history,
        calculate_fitness_metrics,
        search_wger_exercises,
        generate_workout_image,
        generate_workout_video,
        PreloadMemoryTool(),
    ],
    after_model_callback=a2ui_callback,
    after_agent_callback=generate_memories_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
