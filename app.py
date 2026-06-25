import logging
import os
import re
from collections import Counter
from io import BytesIO

try:
    import PyPDF2 as pdf_lib
except ImportError:  # fall back to the modern, maintained package
    import pypdf as pdf_lib

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

load_dotenv()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 8 * 1024 * 1024  # 8 MB upload cap

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("careercopilot")


SKILL_KEYWORDS = {
    "python", "java", "javascript", "typescript", "c", "c++", "c#", "sql",
    "html", "css", "react", "node.js", "node", "express", "django", "flask",
    "fastapi", "streamlit", "pandas", "numpy", "matplotlib", "seaborn",
    "scikit-learn", "sklearn", "tensorflow", "pytorch", "keras",
    "machine learning", "deep learning", "nlp", "natural language processing",
    "computer vision", "data analysis", "data visualization", "data science",
    "statistics", "excel", "power bi", "tableau", "git", "github", "docker",
    "kubernetes", "aws", "azure", "gcp", "linux", "rest api", "api",
    "mongodb", "postgresql", "mysql", "sqlite", "firebase", "oop",
    "object oriented programming", "dsa", "data structures", "algorithms",
    "problem solving", "communication", "teamwork", "leadership", "agile",
    "scrum", "testing", "unit testing",
}


STOP_WORDS = {
    "the", "and", "for", "with", "you", "our", "are", "will", "this",
    "that", "from", "have", "has", "your", "can", "job", "role", "work",
    "team", "candidate", "experience", "skills", "required", "preferred",
    "responsibilities", "requirements",
}


def normalize_text(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+#.\s-]", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def extract_pdf_text(file_bytes: bytes) -> str:
    if not file_bytes:
        return ""
    reader = pdf_lib.PdfReader(BytesIO(file_bytes))
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages).strip()


def keyword_in_text(keyword: str, text: str) -> bool:
    escaped = re.escape(keyword.lower())
    return re.search(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text) is not None


def extract_skills(text: str) -> list:
    normalized = normalize_text(text)
    found = {skill for skill in SKILL_KEYWORDS if keyword_in_text(skill, normalized)}
    aliases = {
        "sklearn": "scikit-learn",
        "node": "node.js",
        "natural language processing": "nlp",
        "object oriented programming": "oop",
        "data structures": "dsa",
    }
    cleaned = {aliases.get(skill, skill) for skill in found}
    return sorted(cleaned)


def extract_important_terms(text: str, limit: int = 20) -> list:
    normalized = normalize_text(text)
    words = re.findall(r"[a-z][a-z0-9+#.-]{2,}", normalized)
    counts = Counter(word for word in words if word not in STOP_WORDS)
    return [word for word, _ in counts.most_common(limit)]


def calculate_ats_score(jd_skills, resume_skills, jd_terms, resume_text) -> int:
    if not jd_skills and not jd_terms:
        return 0

    resume_skill_set = set(resume_skills)
    skill_score = 0
    if jd_skills:
        skill_score = len(resume_skill_set.intersection(jd_skills)) / len(set(jd_skills))

    normalized_resume = normalize_text(resume_text)
    term_score = 0
    if jd_terms:
        matched_terms = [term for term in jd_terms if keyword_in_text(term, normalized_resume)]
        term_score = len(matched_terms) / len(jd_terms)

    score = (skill_score * 0.75) + (term_score * 0.25)
    return round(score * 100)


def build_improvement_suggestions(missing_skills, score) -> list:
    suggestions = []
    if missing_skills:
        visible_skills = ", ".join(missing_skills[:8])
        suggestions.append(f"Add relevant missing keywords where truthful: {visible_skills}.")
    if score < 70:
        suggestions.append("Rewrite project bullets to mirror the JD language and show measurable impact.")
    suggestions.append("Place your strongest matching skills in a dedicated Skills section near the top.")
    suggestions.append("Use action verbs and include tools, outcomes, and numbers in project descriptions.")
    suggestions.append("Keep the resume clean, single-column, and easy for ATS parsers to read.")
    return suggestions


def local_cover_letter(name, role, company, matched_skills, missing_skills) -> str:
    candidate_name = name or "Your Name"
    target_role = role or "the open position"
    company_name = company or "your company"
    skill_line = ", ".join(matched_skills[:6]) if matched_skills else "my academic projects, problem-solving ability, and eagerness to learn"
    growth_line = ""
    if missing_skills:
        growth_line = f" I am also actively strengthening my knowledge of {', '.join(missing_skills[:3])} to better match the role's expectations."

    return f"""Dear Hiring Manager,

I am writing to apply for {target_role} at {company_name}. As a fresher, I bring a strong learning mindset, hands-on project experience, and a genuine interest in building practical solutions.

My background aligns with this role through {skill_line}. I enjoy turning requirements into working features, debugging problems carefully, and improving my work through feedback.{growth_line}

I would be excited to contribute to {company_name} while continuing to grow as a professional. Thank you for considering my application. I look forward to the opportunity to discuss how I can add value to your team.

Sincerely,
{candidate_name}"""


def ai_cover_letter(provider: str, prompt: str):
    try:
        if provider == "OpenAI" and os.getenv("OPENAI_API_KEY"):
            from openai import OpenAI

            client = OpenAI()
            response = client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You write concise, honest fresher-friendly cover letters."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
            )
            return response.choices[0].message.content.strip()

        if provider == "Gemini" and os.getenv("GEMINI_API_KEY"):
            from google import genai

            client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
            response = client.models.generate_content(
                model=os.getenv("GEMINI_MODEL", "gemini-2.0-flash"),
                contents=prompt,
            )
            return response.text.strip()
    except Exception as exc:  # noqa: BLE001
        print(f"AI cover letter generation failed, using local fallback. Details: {exc}")

    return None


def make_cover_letter(provider, name, role, company, jd_text, resume_text, matched_skills, missing_skills) -> str:
    prompt = f"""
Create a customized cover letter for a fresher.

Candidate name: {name or "Your Name"}
Target role: {role or "Not specified"}
Company: {company or "Not specified"}
Matched skills: {", ".join(matched_skills) or "Not detected"}
Missing skills to mention only as learning goals, not fake experience: {", ".join(missing_skills[:6]) or "None"}

Job description:
{jd_text[:2500]}

Resume text:
{resume_text[:2500]}

Rules:
- Keep it under 220 words.
- Make it specific to the role.
- Do not invent experience.
- Sound confident but suitable for a fresher.
"""
    generated = ai_cover_letter(provider, prompt)
    if generated:
        return generated
    return local_cover_letter(name, role, company, matched_skills, missing_skills)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/health")
def health():
    """Quick endpoint to confirm the server is reachable from the browser."""
    return jsonify({"status": "ok"})


@app.before_request
def log_incoming_request():
    logger.info("Incoming request: %s %s", request.method, request.path)


@app.errorhandler(413)
def handle_too_large(_err):
    return jsonify({"error": "That file is too large. Please upload a resume under 8 MB."}), 413


@app.errorhandler(404)
def handle_not_found(_err):
    return jsonify({"error": "Not found."}), 404


@app.errorhandler(Exception)
def handle_unexpected_error(err):
    logger.exception("Unhandled error while processing request")
    return jsonify({"error": f"Unexpected server error: {err}"}), 500


@app.route("/api/analyze", methods=["POST"])
def analyze():
    try:
        resume_file = request.files.get("resume")
        jd_text = (request.form.get("jd_text") or "").strip()
        candidate_name = (request.form.get("candidate_name") or "").strip()
        target_role = (request.form.get("target_role") or "").strip()
        company_name = (request.form.get("company_name") or "").strip()
        provider = (request.form.get("provider") or "Local fallback").strip()

        if not resume_file or resume_file.filename == "":
            return jsonify({"error": "Please upload your resume PDF."}), 400
        if not jd_text:
            return jsonify({"error": "Please paste a job description."}), 400

        try:
            resume_text = extract_pdf_text(resume_file.read())
        except Exception:  # noqa: BLE001
            logger.exception("Failed to parse uploaded PDF")
            return jsonify({"error": "Could not read this PDF. Please upload a valid PDF file."}), 400

        if not resume_text:
            return jsonify({"error": "Could not extract text from this PDF. Try uploading a text-based resume PDF."}), 400

        jd_skills = extract_skills(jd_text)
        resume_skills = extract_skills(resume_text)
        jd_terms = extract_important_terms(jd_text)
        matched_skills = sorted(set(jd_skills).intersection(resume_skills))
        missing_skills = sorted(set(jd_skills).difference(resume_skills))
        score = calculate_ats_score(jd_skills, resume_skills, jd_terms, resume_text)
        suggestions = build_improvement_suggestions(missing_skills, score)

        selected_provider = provider if provider in {"OpenAI", "Gemini"} else "Local fallback"
        cover_letter = make_cover_letter(
            selected_provider,
            candidate_name,
            target_role,
            company_name,
            jd_text,
            resume_text,
            matched_skills,
            missing_skills,
        )

        logger.info("Analysis complete: score=%s matched=%d missing=%d", score, len(matched_skills), len(missing_skills))

        return jsonify({
            "score": score,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "jd_skills": jd_skills,
            "jd_terms": jd_terms,
            "resume_skills": resume_skills,
            "suggestions": suggestions,
            "cover_letter": cover_letter,
        })
    except Exception as err:  # belt-and-suspenders: never let this route return a non-JSON 500
        logger.exception("Unhandled error inside /api/analyze")
        return jsonify({"error": f"Unexpected server error: {err}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", "5000"))
    print(f"\n  CareerCopilot is starting...\n  Open this in your browser: http://127.0.0.1:{port}\n")
    app.run(host="0.0.0.0", port=port, debug=True)
