import os
import streamlit as st
import groq
from typing import Optional
from dotenv import load_dotenv
from groq import Groq

load_dotenv()  # reads your .env file so the API key becomes available to your code

MODEL_NAME = "openai/gpt-oss-20b"

EQUIPMENT_DETAILS = {
    "No equipment": "Bodyweight only. No dumbbells, bands, bench, pull-up bar or any other gear. Floor space only.",
    "Home dumbbells": "A pair (or a few pairs) of dumbbells and floor space only. NO bench, barbell, bands, machines, cables or pull-up bar.",
    "Full gym": "Full commercial gym: barbells, dumbbells, cables, machines, benches, pull-up bar.",
}

GOAL_GUIDANCE = {
    "Build muscle": "Hypertrophy focus: 8-12 reps, 60-90 s rest, progressive overload.",
    "Lose fat": "Fat-loss focus: full-body or circuit style, 12-15 reps, 30-45 s rest, include short conditioning finishers.",
    "General fitness": "Balanced mix of strength, mobility and light cardio, 10-15 reps.",
    "Improve endurance": "Endurance focus: mix cardio/conditioning sessions with high-rep strength work (15-20 reps, short rest). Not every day should be a bodybuilding split.",
}

SYSTEM_PROMPT = """
You are an experienced strength and conditioning coach writing a weekly workout plan for a real person.

HARD RULES (never break these):
1. EQUIPMENT: Use ONLY the equipment described by the user. Never include an exercise that needs
   gear they don't have. If a classic exercise needs missing gear, replace it with a version that
   works with what they have. Dumbbell hip thrusts need a bench, so use floor glute bridges instead.
2. DAYS: Schedule EXACTLY the number of training days requested, no more and no fewer. Label them
   Day 1, Day 2, and so on. Mention rest days in one line at the end. Do not assign weekdays.
   Just say rest days go between hard sessions.
3. INJURIES: If injuries or limitations are given, treat them as strict rules. Do NOT include any
   exercise that directly loads the affected area or breaks the stated restriction. Also avoid
   exercises that are close variations of it (for example, "no overhead pressing" also rules out
   any movement that takes the weight overhead, such as pullovers or raises above shoulder height).
   Choose safer alternatives instead. Never write "shallow" or "partial" versions of a banned movement.
4. EXPERIENCE: Beginner = simple, stable exercises, 2-3 sets, lower volume.
   Intermediate = moderate variety, 3-4 sets.
   Advanced = higher volume and more demanding variations, 4-5 sets.
5. GOAL: Match exercise selection, rep ranges and rest times to the stated goal.
6. NO MEDICAL ADVICE: Do not diagnose, give joint-angle prescriptions, or claim an exercise treats,
   heals or rehabilitates anything. Never mention degrees or joint angles. Do not explain medical reasoning.
7. VARIETY: Don't repeat an identical session on different days. If a muscle group is trained twice,
   vary the exercises or the rep ranges.

OUTPUT FORMAT (Markdown only):
- Start directly with a one-line weekly overview. No greeting and no long introduction.
- For each training day, use a heading like "## Day 1: Upper Body Push", followed by a table with
  the columns: Exercise | Sets | Reps | Rest | Notes
- Keep "Notes" to a short phrase (form cue or substitution).
- Each day: 5 to 7 exercises, plus one line for a quick warm-up.
- End with a "Rest days" line and one short progression tip.
- Keep notes short and write no introduction paragraphs.

Before answering, silently check every exercise against rules 1 and 3.
"""


class PlanGenerationError(Exception):
    """Raised when a plan can't be generated. The message is safe to show to users."""


def validate_inputs(days: Optional[int], equipment: str) -> Optional[str]:
    """Return an error message if the inputs are invalid, otherwise None."""
    if not days or days < 1:
        return "Please choose at least 1 training day per week."
    if not equipment:
        return "Please select your equipment access."
    return None


def build_user_prompt(
    goal: str,
    experience: str,
    days: int,
    equipment: str,
    injuries: str,
) -> str:
    """Turn the structured inputs into the user message sent to the model."""
    equipment_description = EQUIPMENT_DETAILS.get(equipment, equipment)
    if injuries.strip():
        injury_line = f"Injuries / limitations (STRICT constraints): {injuries.strip()}"
    else:
        injury_line = "Injuries / limitations: none reported"

    return (
        f"Goal: {goal}. {GOAL_GUIDANCE[goal]}\n"
        f"Experience level: {experience}\n"
        f"Training days per week: {days}\n"
        f"Equipment available: {equipment_description}\n"
        f"{injury_line}\n\n"
        f"Write my {days}-day weekly workout plan."
    )


def generate_plan(
    goal: str,
    experience: str,
    days: int,
    equipment: str,
    injuries: str,
) -> str:
    """Build a prompt from the user's inputs, call Groq, and return the plan text."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise PlanGenerationError(
            "No API key found. Add GROQ_API_KEY to your .env file and restart the app."
        )

    user_prompt = build_user_prompt(goal, experience, days, equipment, injuries)

    try:
        client = Groq(api_key=api_key)
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
            max_completion_tokens=8000,
            reasoning_effort="low",
        )
        choice = response.choices[0]
        plan = choice.message.content
    except groq.AuthenticationError as e:
        raise PlanGenerationError("Your API key was rejected. Please check it in your .env file.") from e
    except groq.RateLimitError as e:
        raise PlanGenerationError("Too many requests right now. Please wait a minute and try again.") from e
    except groq.NotFoundError as e:
        raise PlanGenerationError("The AI model is unavailable. Please update MODEL_NAME in the code.") from e
    except groq.APIConnectionError as e:
        raise PlanGenerationError("Couldn't reach the AI service. Check your internet connection and try again.") from e
    except groq.APIStatusError as e:
        raise PlanGenerationError(f"The AI service returned an error (code {e.status_code}). Please try again.") from e
    except (IndexError, AttributeError) as e:
        raise PlanGenerationError("The AI response was in an unexpected format. Please try again.") from e

    if choice.finish_reason == "length":
        raise PlanGenerationError("The plan was cut off before it finished. Please try again.")

    if not plan or len(plan.strip()) < 50:
        raise PlanGenerationError("The AI returned an empty or incomplete plan. Please try again.")

    return plan.strip()


def generate_and_store(
    goal: str,
    experience: str,
    days: int,
    equipment: str,
    injuries: str,
) -> bool:
    """Generate a plan and save it in session state. Returns True on success."""
    try:
        with st.spinner("Building your plan..."):
            st.session_state["plan"] = generate_plan(goal, experience, days, equipment, injuries)
        st.session_state["had_injuries"] = bool(injuries.strip())
        return True
    except PlanGenerationError as e:
        st.error(str(e))
        return False


# ---------------------------------------------------------------- UI

st.set_page_config(page_title="Workout Plan Generator", page_icon="💪")

# Optional: makes the bordered containers look like white cards.
# Delete this block if you don't like it or it stops working after a Streamlit upgrade.
st.markdown(
    """
    <style>
    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #FFFFFF;
        border-radius: 16px;
        box-shadow: 0 2px 12px rgba(79, 70, 229, 0.08);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## ❤️ Fitness Planner")
    st.caption("Small steps. Big changes.")
    st.divider()
    with st.expander("About"):
        st.write(
            "Generates a weekly workout plan from your goal, experience, "
            "schedule, equipment and limitations, using an LLM via the Groq API. "
            "General guidance only, not medical advice."
        )

st.title("Your Personalized Workout Plan")
st.caption("Let's create a plan that fits your goals and lifestyle! 💪")

left, right = st.columns([3, 2], gap="large")

with left:
    with st.container(border=True):
        st.subheader("Your Details")
        goal = st.selectbox("Fitness goal", ["Build muscle", "Lose fat", "General fitness", "Improve endurance"])
        experience = st.selectbox("Experience level", ["Beginner", "Intermediate", "Advanced"])
        days = st.pills("Available days per week", options=[1, 2, 3, 4, 5, 6, 7], default=3)
        equipment = st.selectbox("Equipment access", ["No equipment", "Home dumbbells", "Full gym"])
        injuries = st.text_area(
            "Injuries or limitations (optional)",
            placeholder="e.g. bad knees, no overhead pressing",
        )
        generate_clicked = st.button("✨ Generate Plan", type="primary", use_container_width=True)

with right:
    with st.container(border=True):
        st.markdown("# 🏋️‍♀️")
        st.markdown("### Your Fitness Journey Starts Here!")
        st.caption("Pick your details, hit generate, and get a plan you can actually follow.")

if generate_clicked:
    input_error = validate_inputs(days, equipment)
    if input_error:
        st.warning(input_error)
    else:
        generate_and_store(goal, experience, days, equipment, injuries)

if "plan" in st.session_state:
    st.markdown(st.session_state["plan"])

    if st.session_state.get("had_injuries"):
        st.info(
            "⚠️ This plan is general fitness guidance, not medical advice. "
            "Please consult a doctor or physiotherapist about your injury before training."
        )

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        st.download_button(
            "⬇️ Download plan (.md)",
            data=st.session_state["plan"],
            file_name="workout_plan.md",
            mime="text/markdown",
            use_container_width=True,
        )
    with col_b:
        regenerate_clicked = st.button("🔄 Regenerate", use_container_width=True)

    if regenerate_clicked:
        input_error = validate_inputs(days, equipment)
        if input_error:
            st.warning(input_error)
        elif generate_and_store(goal, experience, days, equipment, injuries):
            st.rerun()
