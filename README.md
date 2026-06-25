# CareerCopilot — AI Resume & Job Match Studio

A web app for freshers that compares a resume against a job description,
finds missing keywords, estimates an ATS-style match score, suggests resume
improvements, and generates a customized cover letter.

This version replaces the original Streamlit UI with a custom **Flask + HTML/CSS/JS**
front end: animated gradient UI, a live ATS-score gauge, glass-card panels, and a
fully responsive layout that looks and behaves the same way on desktop and mobile.

## Features

- Drag-and-drop PDF resume upload.
- Paste any job description.
- Extracts skills and role keywords from both documents.
- Calculates an ATS-style match score, shown as an animated gradient gauge.
- Shows matched and missing keywords as colour-coded chips.
- Suggests resume improvement actions.
- Generates a cover letter using OpenAI, Gemini, or a local fallback template.
- Modern animated UI: gradient text, glassmorphism cards, hover/scroll motion,
  large readable type, fully responsive (same look on phone and desktop).

## Tech Stack

- Python 3 + Flask (backend API)
- pypdf / PyPDF2 (resume PDF text extraction)
- Vanilla HTML, CSS, and JavaScript front end (no build step required)
- Optional OpenAI API
- Optional Gemini API

## Open and run this in VS Code

1. **Unzip** this folder and open it in VS Code: `File → Open Folder...`
2. Open a terminal in VS Code: `` Terminal → New Terminal `` (or `` Ctrl+` ``).
3. Create a virtual environment and install dependencies:

   ```bash
   python -m venv .venv
   ```

   Activate it:
   - Windows: `.venv\Scripts\activate`
   - macOS/Linux: `source .venv/bin/activate`

   Then install the requirements:

   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Enable AI-generated cover letters:

   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # macOS/Linux
   ```

   Then add `OPENAI_API_KEY` or `GEMINI_API_KEY` inside `.env`. This step is
   optional — the app works fully without any keys, using a local cover-letter
   template instead.

5. **Run the app:**

   ```bash
   python app.py
   ```

6. Open the URL shown in the terminal — normally **http://127.0.0.1:5000**.

That's it — no npm install, no build step. The front end is plain HTML/CSS/JS
served directly by Flask.

## Project Structure

```
careercopilot/
├── app.py                 # Flask app: routes + resume/JD analysis logic
├── requirements.txt
├── .env.example
├── templates/
│   └── index.html         # Page markup
└── static/
    ├── css/style.css      # Design system, animations, responsive layout
    └── js/app.js          # Form handling, API calls, gauge/chip animations
```

## How It Works

1. You paste a job description and upload a resume PDF in the browser.
2. The front end sends both to the `/api/analyze` Flask endpoint.
3. The backend extracts text from the PDF, detects known skill keywords in
   both documents, and compares them.
4. It calculates an ATS-style score, finds matched/missing skills, and builds
   improvement suggestions.
5. It generates a cover letter (AI provider if configured, otherwise a local
   fallback template).
6. The front end animates the score into a gradient gauge and renders the
   results — skills, suggestions, keywords, and the cover letter — without a
   page reload.

## Notes

The ATS score is a helpful estimate, not an official score from any hiring
platform. Keep the resume honest: only add skills, tools, or achievements you
can actually discuss in an interview.
