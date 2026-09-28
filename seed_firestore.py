import datetime
from google.cloud import firestore

# Hardcoded project ID as required (do not use google.auth.default() or GOOGLE_CLOUD_PROJECT)
PROJECT_ID = "qwiklabs-gcp-02-b47f165a173c"


def seed_database():
    db = firestore.Client(project=PROJECT_ID)

    exercises = [
        {
            "id": "ex_bench_press",
            "name": "Barbell Bench Press",
            "category": "Chest",
            "difficulty": "Intermediate",
            "equipment": "Barbell",
            "target_muscles": ["Pectoralis Major", "Triceps", "Anterior Deltoids"],
            "description": "Lie flat on bench, lower barbell to mid-chest with elbows at 45-degree angle, then press up dynamically.",
            "default_sets_reps": "3-4 sets of 8-10 reps",
        },
        {
            "id": "ex_goblet_squat",
            "name": "Goblet Squat",
            "category": "Legs",
            "difficulty": "Beginner",
            "equipment": "Kettlebell / Dumbbell",
            "target_muscles": ["Quadriceps", "Glutes", "Core"],
            "description": "Hold weight vertically against chest, squat down keeping torso upright, push knees outwards.",
            "default_sets_reps": "3 sets of 10-12 reps",
        },
        {
            "id": "ex_pullup",
            "name": "Pull-ups",
            "category": "Back",
            "difficulty": "Intermediate",
            "equipment": "Pull-up Bar",
            "target_muscles": ["Latissimus Dorsi", "Biceps", "Rhomboids"],
            "description": "Grasp bar slightly wider than shoulder-width, pull chest toward bar squeezing shoulder blades.",
            "default_sets_reps": "3 sets of 6-10 reps",
        },
        {
            "id": "ex_overhead_press",
            "name": "Standing Dumbbell Overhead Press",
            "category": "Shoulders",
            "difficulty": "Intermediate",
            "equipment": "Dumbbell",
            "target_muscles": ["Deltoids", "Triceps", "Upper Chest"],
            "description": "Stand tall with core tight, press dumbbells overhead until arms are fully extended.",
            "default_sets_reps": "3 sets of 8-10 reps",
        },
        {
            "id": "ex_romanian_deadlift",
            "name": "Romanian Deadlift",
            "category": "Hamstrings & Glutes",
            "difficulty": "Intermediate",
            "equipment": "Barbell / Dumbbell",
            "target_muscles": ["Hamstrings", "Gluteus Maximus", "Lower Back"],
            "description": "Hinge at hips pushing glutes back, lower weight along shins with slight knee bend, return by driving hips forward.",
            "default_sets_reps": "3 sets of 8-12 reps",
        },
    ]

    print(f"Seeding 'exercises' collection in Firestore project '{PROJECT_ID}'...")
    for item in exercises:
        doc_ref = db.collection("exercises").document(item["id"])
        doc_ref.set(item)
        print(f"  - Added exercise: {item['name']} ({item['id']})")

    # Seed sample workout log
    sample_log = {
        "id": "log_sample_01",
        "user_id": "user_demo",
        "exercise_name": "Barbell Bench Press",
        "sets": 3,
        "reps": 10,
        "weight_lbs": 155.0,
        "notes": "Felt good, solid chest pump",
        "logged_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
    }
    db.collection("workout_logs").document(sample_log["id"]).set(sample_log)
    print(f"  - Added sample workout log: {sample_log['id']}")

    print("Firestore seeding complete! ✅")


if __name__ == "__main__":
    seed_database()
