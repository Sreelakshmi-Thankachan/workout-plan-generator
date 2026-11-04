# 💪 Workout Plan Generator

A Streamlit web app that creates a personalised weekly workout plan. You tell it your goal,
experience level, available days, equipment and any injuries, and an AI model (via the Groq API)
returns a day-by-day plan with exercises, sets, reps and rest times.

## What the app does (in simple words)

1. You fill in a short form about yourself.
2. The app checks your answers and shows a friendly message if something is missing.
3. It sends your details to an AI model with carefully written instructions.
4. The AI replies with a structured plan, shown day by day.
5. You can regenerate a different version or download the plan as a file.

## Features

- Structured inputs: goal, experience, days per week, equipment, and optional injuries
- Input validation with friendly messages
- Prompt designed to respect equipment, injury and schedule constraints
- Error handling for bad API key, no internet, rate limits, model problems, and empty or cut-off replies
- Plan stays on screen while you use the page (`st.session_state`)
- Regenerate button and download as `.md`
- Injury disclaimer that always appears when injuries are entered

## Main technologies

| Technology | Used for |
|---|---|
| Python 3 | Application logic, type hints, error handling |
| Streamlit | The web interface |
| Groq API | Fast access to the language model (`openai/gpt-oss-20b`) |
| python-dotenv | Loading the API key from a `.env` file |

## Run it locally

1. Clone the repo and open the folder:
   ```
   git clone https://github.com/YOUR_USERNAME/workout-plan-generator.git
   cd workout-plan-generator
   ```
2. Create and activate a virtual environment (Windows):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```
   On Mac/Linux, activate with `source venv/bin/activate`.
3. Install the packages:
   ```
   pip install -r requirements.txt
   ```
4. Get a free API key at https://console.groq.com, then copy `.env.example` to `.env` and put your key in it:
   ```
   GROQ_API_KEY=your_key_here
   ```
5. Start the app:
   ```
   streamlit run app.py
   ```

## How to deploy it (Streamlit Community Cloud, free)

1. Push this repo to GitHub (it must not contain your `.env` file).
2. Go to https://share.streamlit.io and sign in with GitHub.
3. Click **Create app**, choose this repository, branch `main`, and main file `app.py`.
4. Open **Advanced settings → Secrets** and add:
   ```
   GROQ_API_KEY = "your_key_here"
   ```
5. Click **Deploy**. After a few minutes you get a public link.

Never commit your API key. Always keep it in `.env` locally or in the host's secrets settings.

## Prompt design notes

I tested the app with different inputs and improved the prompt step by step.

- **First version:** a one-line prompt. The plan looked good but ignored my constraints:
  it included bands and a bench for a "home dumbbells" user, and squats and lunges for "bad knees".
- **Equipment:** the model didn't know what each option excluded. I added an explicit description for each
  equipment level (for example, no bench or bands for "Home dumbbells").
- **Injuries:** "no overhead pressing" was followed only by name; pullovers and high front raises still
  appeared. I made the rule cover close variations and banned "shallow" or "partial" versions of banned moves.
- **Output format:** I specified a heading per day and a table with fixed columns, which made plans easy to follow.
- **Goals:** "Improve endurance" was producing a bodybuilding split, so I added guidance per goal (reps, rest, style).
- **Cut-off plans:** longer plans stopped mid-table. The cause was a word limit that contradicted the task, plus
  the model using its output budget for reasoning. I removed the word limit, raised the token limit,
  lowered reasoning effort, and added a check that shows an error if a plan is incomplete.
- **Medical scope:** the model gave joint-angle advice and invented medical reasons. I banned medical claims in
  the prompt, and the disclaimer is added by code so it always appears when injuries are entered.
- **Lesson:** things that must always happen (disclaimer, validation) belong in code; the prompt is for judgement.

## Limitations

- General fitness guidance only, not medical advice.
- AI output can still occasionally break a rule, so users should review the plan before following it.
- [Add anything else you noticed]
