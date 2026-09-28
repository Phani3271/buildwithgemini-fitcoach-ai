import datetime
import json
import os
import urllib.request
from google import genai
from google.adk.tools import ToolContext
from google.cloud import firestore, storage
from google.genai import types

# Hardcoded project ID and Cloud Storage bucket name as strings
# (DO NOT read from google.auth.default() or GOOGLE_CLOUD_PROJECT to prevent Agent Platform issues)
PROJECT_ID = "qwiklabs-gcp-02-b47f165a173c"
BUCKET_NAME = "fitcoach-ai-assets-qwiklabs-gcp-02-b47f165a173c"


def _get_db():
    return firestore.Client(project=PROJECT_ID)


def search_exercise_catalog(category: str = "", muscle: str = "") -> list[dict]:
    """Search the exercise database in Firestore by category or targeted muscle.

    Args:
        category: Filter by exercise category (e.g., 'Chest', 'Legs', 'Back', 'Shoulders').
        muscle: Filter by targeted muscle group (e.g., 'Pectoralis Major', 'Quadriceps', 'Biceps').

    Returns:
        List of matching exercise dictionaries with details.
    """
    db = _get_db()
    docs = db.collection("exercises").stream()

    results = []
    for doc in docs:
        data = doc.to_dict()
        category_match = not category or category.lower() in data.get("category", "").lower()
        
        target_muscles = [m.lower() for m in data.get("target_muscles", [])]
        muscle_match = not muscle or any(muscle.lower() in m for m in target_muscles)

        if category_match and muscle_match:
            results.append(data)

    return results


def get_exercise_details(exercise_name: str) -> dict:
    """Get full details for a specific exercise from the Firestore catalog.

    Args:
        exercise_name: The name or partial name of the exercise.

    Returns:
        Dictionary containing exercise details if found, or an error message dict.
    """
    db = _get_db()
    docs = db.collection("exercises").stream()

    for doc in docs:
        data = doc.to_dict()
        if exercise_name.lower() in data.get("name", "").lower():
            return data

    return {"error": f"No exercise found matching '{exercise_name}'."}


def log_workout(
    exercise_name: str,
    sets: int,
    reps: int,
    weight_lbs: float,
    notes: str = "",
) -> str:
    """Log a completed workout set/session into the Firestore database.

    Args:
        exercise_name: Name of the exercise performed (e.g., 'Barbell Bench Press').
        sets: Number of sets completed.
        reps: Number of reps completed per set.
        weight_lbs: Weight used in pounds.
        notes: Optional user notes or feedback on performance.

    Returns:
        Confirmation string with details of the logged entry.
    """
    db = _get_db()
    log_id = f"log_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
    
    log_data = {
        "id": log_id,
        "user_id": "user_demo",
        "exercise_name": exercise_name,
        "sets": sets,
        "reps": reps,
        "weight_lbs": weight_lbs,
        "notes": notes,
        "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }

    db.collection("workout_logs").document(log_id).set(log_data)
    return f"Successfully logged workout '{exercise_name}': {sets} sets x {reps} reps @ {weight_lbs} lbs. Log ID: {log_id}"


def get_workout_history(limit: int = 5) -> list[dict]:
    """Retrieve recent logged workouts from Firestore.

    Args:
        limit: Maximum number of recent workout entries to return (default: 5).

    Returns:
        List of recent workout log dictionaries.
    """
    db = _get_db()
    docs = (
        db.collection("workout_logs")
        .order_by("logged_at", direction=firestore.Query.DESCENDING)
        .limit(limit)
        .stream()
    )

    return [doc.to_dict() for doc in docs]


def calculate_fitness_metrics(
    metric_type: str,
    weight_lbs: float,
    height_inches: float = 70.0,
    age: int = 30,
    gender: str = "male",
    resting_hr: int = 60,
    reps: int = 1,
) -> dict:
    """Calculate fitness and health metrics including BMR, TDEE, Target Heart Rate (Karvonen), or 1-Rep Max (1RM).

    Args:
        metric_type: Type of metric to calculate ('bmr_tdee', 'heart_rate_zones', or 'one_rep_max').
        weight_lbs: Weight in pounds.
        height_inches: Height in inches (required for BMR/TDEE).
        age: Age in years (required for heart rate zones and BMR).
        gender: Gender ('male' or 'female') for BMR formula.
        resting_hr: Resting heart rate in bpm for Karvonen formula.
        reps: Number of reps completed (for one_rep_max calculation).

    Returns:
        Dictionary containing calculated fitness metrics and target ranges.
    """
    m_type = metric_type.lower()

    if "one_rep_max" in m_type or "1rm" in m_type:
        # Epley Formula for 1RM estimation
        if reps <= 1:
            est_1rm = weight_lbs
        else:
            est_1rm = round(weight_lbs * (1 + reps / 30.0), 1)
        return {
            "metric": "1-Rep Max Estimation (Epley)",
            "weight_lifted_lbs": weight_lbs,
            "reps_completed": reps,
            "estimated_1rm_lbs": est_1rm,
        }

    elif "heart" in m_type or "hr" in m_type:
        # Karvonen Formula for Heart Rate Zones
        max_hr = 220 - age
        hrr = max_hr - resting_hr
        zone2_min = round(resting_hr + (hrr * 0.60))
        zone2_max = round(resting_hr + (hrr * 0.70))
        zone3_max = round(resting_hr + (hrr * 0.80))
        return {
            "metric": "Target Heart Rate Zones (Karvonen Formula)",
            "age": age,
            "resting_hr_bpm": resting_hr,
            "estimated_max_hr_bpm": max_hr,
            "fat_burn_zone_2_bpm": f"{zone2_min} - {zone2_max} bpm (60-70% HRR)",
            "aerobic_zone_3_bpm": f"{zone2_max + 1} - {zone3_max} bpm (70-80% HRR)",
        }

    else:
        # BMR (Mifflin-St Jeor) and TDEE Estimation
        weight_kg = weight_lbs * 0.453592
        height_cm = height_inches * 2.54
        s_factor = 5 if gender.lower() == "male" else -161
        bmr = round((10 * weight_kg) + (6.25 * height_cm) - (5 * age) + s_factor)
        tdee_moderate = round(bmr * 1.55)
        return {
            "metric": "BMR & TDEE Caloric Metrics (Mifflin-St Jeor)",
            "basal_metabolic_rate_bmr": f"{bmr} kcal/day",
            "tdee_moderate_activity": f"{tdee_moderate} kcal/day",
            "suggested_protein_grams": f"{round(weight_lbs * 0.9)} - {round(weight_lbs * 1.0)} g/day",
        }


def search_wger_exercises(query: str = "") -> list[dict]:
    """Search for real public exercise guides and data from the Wger Open Fitness Public API.

    Args:
        query: Search keyword or exercise name to query from the public database (e.g., 'Kettlebell', 'Press').

    Returns:
        List of exercise dictionaries containing real exercise name, category, equipment, and description.
    """
    api_key = os.getenv("WGER_API_KEY", "")
    url = "https://wger.de/api/v2/exerciseinfo/?limit=30"

    headers = {"User-Agent": "FitCoachAI/1.0", "Accept": "application/json"}
    if api_key:
        headers["Authorization"] = f"Token {api_key}"

    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            results = []
            for item in data.get("results", []):
                names = [t.get("name") for t in item.get("translations", []) if t.get("name")]
                desc = ""
                for t in item.get("translations", []):
                    if t.get("description_source"):
                        desc = t.get("description_source")
                        break

                matched_name = names[0] if names else "Exercise"
                category_name = item.get("category", {}).get("name", "General")
                equipment_list = [e.get("name") for e in item.get("equipment", []) if e.get("name")]

                if not query or query.lower() in matched_name.lower() or query.lower() in category_name.lower():
                    results.append({
                        "name": matched_name,
                        "category": category_name,
                        "equipment": equipment_list,
                        "description": desc[:250] + ("..." if len(desc) > 250 else ""),
                    })

                if len(results) >= 5:
                    break
            return results
    except Exception as e:
        return [{"error": f"Failed to fetch exercise data from Wger API: {str(e)}"}]


async def generate_workout_image(
    prompt: str,
    tool_context: ToolContext,
) -> str:
    """Generate a workout or exercise form visual using Gemini Image Generation.

    Args:
        prompt: Detailed prompt describing the workout illustration or exercise form graphic to generate.
        tool_context: ADK ToolContext used to save the artifact for Playground visualization.

    Returns:
        Public HTTPS URL of the generated image uploaded to Cloud Storage.
    """
    client = genai.Client(vertexai=True, location="global", project=PROJECT_ID)
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=prompt,
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                if part.inline_data.mime_type:
                    mime_type = part.inline_data.mime_type
                break

    if not image_bytes:
        return "Error: Failed to generate image bytes."

    filename = f"workout_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}.jpg"

    # 1. Save artifact to ADK ToolContext so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload image bytes directly to public GCS bucket (without saving local file)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"


async def generate_workout_video(
    prompt: str,
    tool_context: ToolContext,
) -> str:
    """Generate a workout or exercise form short video using Google's Omni model (gemini-omni-flash-preview).

    Args:
        prompt: Detailed prompt describing the exercise motion or form demonstration video to generate.
        tool_context: ADK ToolContext used to save the artifact for Playground visualization.

    Returns:
        Public HTTPS URL of the generated video uploaded to Cloud Storage.
    """
    client = genai.Client(vertexai=True, location="global", project=PROJECT_ID)
    res = client.interactions.create(
        model="gemini-omni-flash-preview",
        input=prompt,
    )

    video_bytes = None
    mime_type = "video/mp4"

    if getattr(res, "output_video", None) and getattr(res.output_video, "data", None):
        video_bytes = res.output_video.data
        if getattr(res.output_video, "mime_type", None):
            mime_type = res.output_video.mime_type
    else:
        outputs = getattr(res, "outputs", None) or []
        for output in outputs:
            parts = getattr(output, "parts", None) or []
            if not parts:
                contents = getattr(output, "contents", None) or []
                for content in contents:
                    c_parts = getattr(content, "parts", None) or []
                    if c_parts:
                        parts.extend(c_parts)
            for part in parts:
                inline_data = getattr(part, "inline_data", None)
                if inline_data and getattr(inline_data, "data", None):
                    video_bytes = inline_data.data
                    if getattr(inline_data, "mime_type", None):
                        mime_type = inline_data.mime_type
                    break

    if not video_bytes:
        return "Error: Failed to generate video bytes from Omni model."

    filename = f"workout_video_{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}.mp4"

    # 1. Save artifact to ADK ToolContext so it shows up in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    await tool_context.save_artifact(filename=filename, artifact=artifact_part)

    # 2. Upload video bytes directly to public GCS bucket (without writing a local file)
    storage_client = storage.Client(project=PROJECT_ID)
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    return f"https://storage.googleapis.com/{BUCKET_NAME}/{filename}"



