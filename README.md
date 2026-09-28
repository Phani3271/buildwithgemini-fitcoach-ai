# FitCoach AI — Agentic Fitness & Workout Strategist

![FitCoach AI Demo](demo.gif)

FitCoach AI is an intelligent agentic workout coach and fitness strategist built with Google's Agent Development Kit (ADK). It provides personalized workout plans, logs exercise history to Cloud Firestore, calculates key fitness metrics (1RM, heart rate zones, BMR/TDEE), searches live public exercise databases, generates visual exercise guides and video demonstrations, and maintains long-term memory across chat sessions.

---

## 🛠️ Implemented Features & Tools

Based directly on the implementation in [`app/tools.py`](app/tools.py) and [`app/agent.py`](app/agent.py), FitCoach AI provides the following tools and capabilities:

- **Exercise Catalog & Wger API Integration**:
  - `search_exercise_catalog`: Searches the built-in exercise catalog by muscle group or category.
  - `get_exercise_details`: Fetches detailed execution instructions and tips for specific exercises.
  - `search_wger_exercises`: Queries the live public [Wger REST API](https://wger.de/en/software/api) for extended exercise definitions.
- **Workout Logging & History (Google Cloud Firestore)**:
  - `log_workout`: Persists completed workout sessions (exercise name, sets, reps, weight) into Google Cloud Firestore (`fitcoach-ai-workouts` collection).
  - `get_workout_history`: Queries Firestore to retrieve past workout logs and progress.
- **Fitness Metric Calculators**:
  - `calculate_fitness_metrics`: Computes One-Rep Max (Epley formula), Target Heart Rate zones (Karvonen formula), and BMR/TDEE (Mifflin-St Jeor equation).
- **AI Media Generation**:
  - `generate_workout_image`: Generates high-quality exercise form diagrams using Google's **Imagen 3** model (`imagen-3.0-generate-002`), saves artifacts for Playground inspection, and uploads them to a public Cloud Storage bucket.
  - `generate_workout_video`: Generates short motion videos using Google's **Omni model** (`gemini-omni-flash-preview`), saves artifacts via ADK's `ToolContext`, and uploads the video bytes to a public Cloud Storage bucket.
- **Long-Term Memory (Vertex AI Memory Bank)**:
  - Integrates `VertexAiMemoryBankService` and `PreloadMemoryTool` to automatically extract and remember user preferences, injuries, and health constraints across chat sessions.
- **Structured UI Generation (A2UI)**:
  - Uses `A2uiSchemaManager` (v0.8 BasicCatalog) and `a2ui_callback` to format agent responses as structured JSON cards when appropriate.

---

## ☁️ Google Cloud Services Integrated

- **Vertex AI Agent Engine / Reasoning Engine**: Runtime execution and sandbox code execution.
- **Vertex AI Memory Bank**: Long-term session memory store and retrieval.
- **Google Cloud Firestore**: NoSQL database for workout logs and history.
- **Google Cloud Storage**: Public asset storage for generated images and video demonstrations.
- **Vertex AI Imagen 3 (`imagen-3.0-generate-002`)**: Text-to-image generation.
- **Google Omni (`gemini-omni-flash-preview`)**: Multimodal video generation.

---

## 🚀 Setup & Local Execution

### Prerequisites

- Python 3.10+
- Node.js 18+ (for local frontend)
- Google Cloud SDK (`gcloud`) authenticated to your GCP project with Vertex AI and Firestore APIs enabled.

### 1. Installation

Clone the repository and install dependencies using `uv` or `pip`:

```bash
cd fitcoach-ai
uv sync
```

### 2. Environment Setup

Configure your Google Cloud Project ID:

```bash
export GOOGLE_CLOUD_PROJECT="your-gcp-project-id"
```

### 3. Running the Agent Playground (Dev UI)

To start the ADK agent playground locally:

```bash
uv run adk web . --port 8000 --reload_agents
```

### 4. Running the Web Frontend

To launch the FastAPI proxy server and web frontend:

```bash
cd frontend
uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

Then open your browser to `localhost:8080`.

---

## 📄 Manifest & Architecture

The project configuration lives in `agents-cli-manifest.yaml` and deploys to **Vertex AI Agent Engine** using `agents-cli`:

```yaml
name: fitcoach-ai
acli_version: 1.1.0
agent_directory: app
region: us-east1
base_template: adk
```
