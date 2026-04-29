# """
# CareerAI - Python AI Microservice
# Runs locally. No API keys needed.
# Models: rembg (U2-Net), spaCy NLP, OpenCV face detection

# Install deps:
#   pip install flask flask-cors rembg pillow spacy opencv-python-headless numpy
#   python -m spacy download en_core_web_sm
# """

# from flask import Flask, request, jsonify, send_file
# from flask_cors import CORS
# import base64
# import io
# import json
# import re
# import math
# import os
# import tempfile

# app = Flask(__name__)
# CORS(app)

# # ─────────────────────────────────────────────
# # LAZY MODEL LOADERS  (load once on first use)
# # ─────────────────────────────────────────────
# _nlp = None
# _bg_remover = None

# def get_nlp():
#     global _nlp
#     if _nlp is None:
#         import spacy
#         _nlp = spacy.load("en_core_web_sm")
#     return _nlp

# def get_bg_remover():
#     global _bg_remover
#     if _bg_remover is None:
#         from rembg import new_session
#         _bg_remover = new_session("u2net")  # downloads ~170 MB on first run
#     return _bg_remover


# # ─────────────────────────────────────────────
# # FEATURE 1: BACKGROUND REMOVAL
# # ─────────────────────────────────────────────
# @app.route("/api/remove-bg", methods=["POST"])
# def remove_bg():
#     try:
#         data = request.get_json()
#         if not data or "image" not in data:
#             return jsonify({"error": "No image provided"}), 400

#         # Decode base64 image
#         image_data = data["image"]
#         if "," in image_data:
#             image_data = image_data.split(",", 1)[1]

#         img_bytes = base64.b64decode(image_data)

#         from rembg import remove
#         from PIL import Image

#         input_img = Image.open(io.BytesIO(img_bytes)).convert("RGBA")

#         # Remove background using U2-Net
#         session = get_bg_remover()
#         output_img = remove(input_img, session=session)

#         # Encode result as base64 PNG (preserves transparency)
#         buf = io.BytesIO()
#         output_img.save(buf, format="PNG")
#         buf.seek(0)
#         result_b64 = base64.b64encode(buf.read()).decode("utf-8")

#         return jsonify({
#             "success": True,
#             "image": f"data:image/png;base64,{result_b64}",
#             "format": "png"
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # ─────────────────────────────────────────────
# # FEATURE 2: ATS CHECKER
# # ─────────────────────────────────────────────

# TECH_SKILLS = {
#     "python", "javascript", "typescript", "java", "c++", "c#", "go", "rust",
#     "react", "angular", "vue", "node.js", "express", "django", "flask", "spring",
#     "sql", "mysql", "postgresql", "mongodb", "redis", "elasticsearch",
#     "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
#     "git", "linux", "bash", "rest", "graphql", "microservices",
#     "machine learning", "deep learning", "tensorflow", "pytorch", "scikit-learn",
#     "html", "css", "tailwind", "figma", "agile", "scrum", "ci/cd",
#     "data analysis", "power bi", "tableau", "excel", "communication",
#     "leadership", "problem solving", "teamwork", "project management",
# }

# STOP_WORDS = {
#     "the","and","or","of","to","a","an","in","for","with","on","at","by",
#     "from","as","is","are","was","were","be","been","being","have","has",
#     "had","do","does","did","will","would","could","should","may","might",
#     "shall","can","not","no","but","if","then","that","this","it","its",
#     "we","i","you","they","he","she","our","their","your","my","his","her",
#     "us","them","who","which","what","when","where","how","why","about",
#     "also","more","other","into","through","during","before","after","above",
#     "below","between","out","off","over","under","again","further","once",
# }

# def extract_keywords(text):
#     """Extract meaningful keywords from text using spaCy."""
#     nlp = get_nlp()
#     doc = nlp(text.lower())

#     keywords = set()

#     # Extract noun chunks, named entities, and important tokens
#     for chunk in doc.noun_chunks:
#         phrase = chunk.text.strip()
#         if len(phrase) > 2 and phrase not in STOP_WORDS:
#             keywords.add(phrase)

#     for ent in doc.ents:
#         if ent.label_ in ("ORG", "PRODUCT", "GPE", "SKILL"):
#             keywords.add(ent.text.lower().strip())

#     for token in doc:
#         if (not token.is_stop and not token.is_punct and
#                 token.pos_ in ("NOUN", "PROPN", "VERB") and
#                 len(token.text) > 2):
#             keywords.add(token.lemma_.lower())

#     # Also check for known tech skills as multi-word phrases
#     text_lower = text.lower()
#     for skill in TECH_SKILLS:
#         if skill in text_lower:
#             keywords.add(skill)

#     return keywords


# def compute_tfidf_similarity(resume_text, jd_text):
#     """Simple TF-IDF cosine similarity between resume and JD."""
#     def word_freq(text):
#         words = re.findall(r'\b[a-z]{2,}\b', text.lower())
#         freq = {}
#         for w in words:
#             if w not in STOP_WORDS:
#                 freq[w] = freq.get(w, 0) + 1
#         return freq

#     r_freq = word_freq(resume_text)
#     j_freq = word_freq(jd_text)

#     # Union of all words
#     all_words = set(r_freq.keys()) | set(j_freq.keys())

#     # Cosine similarity
#     dot = sum(r_freq.get(w, 0) * j_freq.get(w, 0) for w in all_words)
#     mag_r = math.sqrt(sum(v**2 for v in r_freq.values()))
#     mag_j = math.sqrt(sum(v**2 for v in j_freq.values()))

#     if mag_r == 0 or mag_j == 0:
#         return 0.0
#     return dot / (mag_r * mag_j)


# def calculate_ats_score(resume_text, jd_text):
#     resume_kw = extract_keywords(resume_text)
#     jd_kw = extract_keywords(jd_text)

#     # Keyword match score (40%)
#     if len(jd_kw) == 0:
#         kw_score = 0.5
#     else:
#         matched = resume_kw & jd_kw
#         kw_score = len(matched) / len(jd_kw)

#     # TF-IDF similarity (40%)
#     tfidf_score = compute_tfidf_similarity(resume_text, jd_text)

#     # Tech skills coverage (20%)
#     jd_lower = jd_text.lower()
#     resume_lower = resume_text.lower()
#     jd_skills = {s for s in TECH_SKILLS if s in jd_lower}
#     resume_skills = {s for s in TECH_SKILLS if s in resume_lower}
#     if len(jd_skills) == 0:
#         skill_score = 1.0
#     else:
#         skill_score = len(resume_skills & jd_skills) / len(jd_skills)

#     total = (kw_score * 0.40) + (tfidf_score * 0.40) + (skill_score * 0.20)
#     final_score = min(int(total * 100), 99)

#     # Missing keywords (prioritise tech skills first)
#     jd_kw_list = list(jd_kw)
#     missing_tech = [s for s in jd_skills if s not in resume_skills]
#     missing_general = [k for k in jd_kw_list if k not in resume_kw and k not in TECH_SKILLS][:10]

#     missing_keywords = missing_tech[:8] + missing_general[:max(0, 12 - len(missing_tech))]
#     matched_keywords = list(resume_kw & jd_kw)[:15]

#     return {
#         "score": final_score,
#         "keyword_match": round(kw_score * 100),
#         "content_similarity": round(tfidf_score * 100),
#         "skills_coverage": round(skill_score * 100),
#         "matched_keywords": matched_keywords,
#         "missing_keywords": missing_keywords,
#     }


# def generate_suggestions(score_data, resume_text, jd_text):
#     suggestions = []

#     if score_data["score"] < 50:
#         suggestions.append({
#             "type": "critical",
#             "title": "Low keyword alignment",
#             "detail": "Your resume shares very few keywords with the job description. Rewrite your summary and skills section to mirror the JD language."
#         })

#     if score_data["missing_keywords"]:
#         top_missing = ", ".join(score_data["missing_keywords"][:5])
#         suggestions.append({
#             "type": "warning",
#             "title": "Add missing keywords",
#             "detail": f"These important terms appear in the JD but not your resume: {top_missing}. Weave them in naturally."
#         })

#     if score_data["skills_coverage"] < 60:
#         suggestions.append({
#             "type": "warning",
#             "title": "Strengthen technical skills section",
#             "detail": "The JD asks for specific technical skills that are missing or under-represented in your resume."
#         })

#     if "quantif" not in resume_text.lower() and not re.search(r'\d+%|\d+x|\$\d+|\d+ year', resume_text):
#         suggestions.append({
#             "type": "info",
#             "title": "Add measurable achievements",
#             "detail": "ATS systems and recruiters reward quantified results. Add numbers: 'Reduced load time by 40%', 'Led team of 8', etc."
#         })

#     if len(resume_text) < 400:
#         suggestions.append({
#             "type": "info",
#             "title": "Expand your resume content",
#             "detail": "Your resume appears short. ATS systems need enough text to analyse. Aim for 400–700 words."
#         })

#     if score_data["score"] >= 75:
#         suggestions.append({
#             "type": "success",
#             "title": "Strong ATS alignment",
#             "detail": "Your resume is well-optimised for this role. Focus on polishing formatting and personalising your summary."
#         })

#     return suggestions


# @app.route("/api/ats-check", methods=["POST"])
# def ats_check():
#     try:
#         data = request.get_json()
#         resume_text = data.get("resume", "").strip()
#         jd_text = data.get("jobDescription", "").strip()

#         if not resume_text or not jd_text:
#             return jsonify({"error": "Both resume and job description are required"}), 400

#         score_data = calculate_ats_score(resume_text, jd_text)
#         suggestions = generate_suggestions(score_data, resume_text, jd_text)

#         return jsonify({
#             "success": True,
#             "score": score_data["score"],
#             "breakdown": {
#                 "keywordMatch": score_data["keyword_match"],
#                 "contentSimilarity": score_data["content_similarity"],
#                 "skillsCoverage": score_data["skills_coverage"],
#             },
#             "matchedKeywords": score_data["matched_keywords"],
#             "missingKeywords": score_data["missing_keywords"],
#             "suggestions": suggestions,
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # ─────────────────────────────────────────────
# # FEATURE 3: HEADSHOT GENERATOR
# # ─────────────────────────────────────────────

# BACKGROUND_COLORS = {
#     "linkedin":    (  8,  76, 138),   # LinkedIn navy
#     "professional":(240, 240, 240),   # Light grey
#     "white":       (255, 255, 255),
#     "dark":        ( 40,  40,  50),
#     "gradient_blue": None,             # handled separately
# }

# def enhance_headshot(pil_img, style="professional"):
#     """
#     Pipeline:
#      1. Detect & crop face (OpenCV DNN or Haar fallback)
#      2. Enhance brightness / contrast
#      3. Sharpen skin / detail
#      4. Replace background with chosen colour
#      5. Add subtle vignette
#     Returns a PIL Image (JPEG-quality enhanced portrait).
#     """
#     import cv2
#     import numpy as np
#     from PIL import Image, ImageEnhance, ImageFilter

#     # ── Convert PIL → OpenCV BGR
#     img_np = np.array(pil_img.convert("RGB"))
#     img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
#     h, w = img_bgr.shape[:2]

#     # ── 1. Face detection ─────────────────────
#     gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
#     face_cascade = cv2.CascadeClassifier(
#         cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
#     )
#     faces = face_cascade.detectMultiScale(
#         gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
#     )

#     if len(faces) == 0:
#         # Profile / side face fallback
#         profile_cascade = cv2.CascadeClassifier(
#             cv2.data.haarcascades + "haarcascade_profileface.xml"
#         )
#         faces = profile_cascade.detectMultiScale(gray, 1.1, 5, minSize=(60, 60))

#     # ── 2. Smart crop (show head + upper shoulders) ─
#     if len(faces) > 0:
#         fx, fy, fw, fh = max(faces, key=lambda f: f[2] * f[3])  # largest face
#         padding_top    = int(fh * 0.6)
#         padding_sides  = int(fw * 0.8)
#         padding_bottom = int(fh * 1.2)

#         x1 = max(0, fx - padding_sides)
#         y1 = max(0, fy - padding_top)
#         x2 = min(w, fx + fw + padding_sides)
#         y2 = min(h, fy + fh + padding_bottom)

#         img_bgr = img_bgr[y1:y2, x1:x2]

#     # ── 3. Resize to portrait dimensions
#     target_h, target_w = 600, 500
#     img_bgr = cv2.resize(img_bgr, (target_w, target_h), interpolation=cv2.INTER_LANCZOS4)

#     # ── 4. Enhance with PIL ───────────────────
#     img_pil = Image.fromarray(cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB))

#     # Brightness
#     img_pil = ImageEnhance.Brightness(img_pil).enhance(1.05)
#     # Contrast
#     img_pil = ImageEnhance.Contrast(img_pil).enhance(1.12)
#     # Colour vibrancy
#     img_pil = ImageEnhance.Color(img_pil).enhance(1.08)
#     # Sharpness
#     img_pil = ImageEnhance.Sharpness(img_pil).enhance(1.4)

#     # ── 5. Background removal + replacement ──
#     from rembg import remove
#     session = get_bg_remover()
#     no_bg = remove(img_pil, session=session)  # RGBA

#     bg_color = BACKGROUND_COLORS.get(style, (240, 240, 240))

#     if style == "gradient_blue":
#         # Create a vertical gradient background
#         bg = Image.new("RGBA", (target_w, target_h))
#         bg_np = np.zeros((target_h, target_w, 4), dtype=np.uint8)
#         for row in range(target_h):
#             t = row / target_h
#             r = int((1 - t) * 10  + t * 30)
#             g = int((1 - t) * 60  + t * 100)
#             b = int((1 - t) * 140 + t * 180)
#             bg_np[row, :] = [r, g, b, 255]
#         bg = Image.fromarray(bg_np, "RGBA")
#     else:
#         bg = Image.new("RGBA", (target_w, target_h), (*bg_color, 255))

#     # Composite subject on background
#     composite = Image.alpha_composite(bg, no_bg)

#     # ── 6. Subtle vignette ───────────────────
#     composite_np = np.array(composite.convert("RGB"), dtype=np.float32)
#     vignette = np.zeros((target_h, target_w), dtype=np.float32)
#     cx, cy = target_w // 2, target_h // 2
#     for y in range(target_h):
#         for x in range(target_w):
#             dx = (x - cx) / cx
#             dy = (y - cy) / cy
#             vignette[y, x] = 1.0 - 0.25 * (dx*dx + dy*dy)
#     vignette = np.clip(vignette, 0, 1)
#     composite_np *= vignette[:, :, np.newaxis]
#     composite_np = np.clip(composite_np, 0, 255).astype(np.uint8)

#     return Image.fromarray(composite_np)


# @app.route("/api/headshot", methods=["POST"])
# def headshot():
#     try:
#         data = request.get_json()
#         if not data or "image" not in data:
#             return jsonify({"error": "No image provided"}), 400

#         image_data = data["image"]
#         if "," in image_data:
#             image_data = image_data.split(",", 1)[1]
#         img_bytes = base64.b64decode(image_data)

#         style = data.get("style", "professional")  # linkedin | professional | white | dark | gradient_blue

#         from PIL import Image
#         pil_img = Image.open(io.BytesIO(img_bytes))

#         enhanced = enhance_headshot(pil_img, style=style)

#         buf = io.BytesIO()
#         enhanced.save(buf, format="JPEG", quality=92, optimize=True)
#         buf.seek(0)
#         result_b64 = base64.b64encode(buf.read()).decode("utf-8")

#         return jsonify({
#             "success": True,
#             "image": f"data:image/jpeg;base64,{result_b64}",
#             "style": style,
#         })

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # ─────────────────────────────────────────────
# # HEALTH CHECK
# # ─────────────────────────────────────────────
# @app.route("/health", methods=["GET"])
# def health():
#     return jsonify({"status": "ok", "service": "CareerAI Python microservice"})



#    # At the bottom, replace your current __main__ block:
# if __name__ == "__main__":
#     print("[CareerAI] Pre-loading U2-Net model...")
#     get_bg_remover()  # load model at startup, not on first request
#     print("[CareerAI] Model ready!")
#     port = int(os.environ.get("PORT", 5001))
#     app.run(host="0.0.0.0", port=port, debug=False)

"""CareerAI - Lightweight AI Service
Uses Hugging Face Inference API for image tasks — no rembg, no opencv, no heavy installs.
ATS checker runs fully local with spaCy (small model, ~15MB).

Deploy this on Render free tier — total install size stays under 200MB.

Install:
  pip install flask flask-cors requests pillow spacy
  python -m spacy download en_core_web_sm
 
Environment variable needed:
  HF_TOKEN=hf_your_token_here  (free at huggingface.co/settings/tokens)
"""

import os
import io
import base64
import math
import re
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)
CORS(app)

HF_TOKEN = os.environ.get("HF_TOKEN", "")
HF_HEADERS = {"Authorization": f"Bearer {HF_TOKEN}"}

# ─── Lazy spaCy loader ────────────────────────────────────────────────────────
_nlp = None
def get_nlp():
    global _nlp
    if _nlp is None:
        import spacy
        _nlp = spacy.load("en_core_web_sm")
    return _nlp


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 1 — BACKGROUND REMOVAL  (HF: briaai/RMBG-1.4)
# ══════════════════════════════════════════════════════════════════════════════

# HF_RMBG_URL = "https://router.huggingface.co/hf-inference/models/briaai/RMBG-1.4"

# def call_hf_remove_bg(image_bytes: bytes) -> bytes:
#     """Send image bytes to HF RMBG-1.4, get back PNG bytes with transparency."""
#     response = requests.post(
#         HF_RMBG_URL,
#         headers={**HF_HEADERS, "Content-Type": "image/jpeg"},
#         data=image_bytes,
#         timeout=60,
#     )
#     if response.status_code == 200:
#         return response.content          # PNG bytes returned by the model
#     # Model loading (503) — wait and retry once
#     if response.status_code == 503:
#         import time
#         time.sleep(20)
#         response = requests.post(
#             HF_RMBG_URL,
#             headers={**HF_HEADERS, "Content-Type": "image/jpeg"},
#             data=image_bytes,
#             timeout=90,
#         )
#         if response.status_code == 200:
#             return response.content
#     raise Exception(f"HF BG removal failed ({response.status_code}): {response.text[:200]}")

#Add this env variable at the top with your other env vars
REMOVE_BG_KEY = os.environ.get("REMOVE_BG_API_KEY", "")

def call_hf_remove_bg(image_bytes: bytes) -> bytes:
    """Uses remove.bg API — 50 free calls/month, no credit card needed."""
    response = requests.post(
        "https://api.remove.bg/v1.0/removebg",
        files={"image_file": ("image.jpg", image_bytes, "image/jpeg")},
        data={"size": "auto"},
        headers={"X-Api-Key": REMOVE_BG_KEY},
        timeout=60,
    )
    if response.status_code == 200:
        return response.content  # returns PNG bytes directly
    raise Exception(f"remove.bg failed ({response.status_code}): {response.text[:200]}")
@app.route("/api/remove-bg", methods=["POST"])
def remove_bg():
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image provided"}), 400

        raw = data["image"]
        if "," in raw:
            raw = raw.split(",", 1)[1]
        img_bytes = base64.b64decode(raw)

        # Resize to max 1024px before sending to save bandwidth & avoid HF limits
        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        MAX = 1024
        if max(pil.size) > MAX:
            pil.thumbnail((MAX, MAX), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=90)
        buf.seek(0)
        resized_bytes = buf.read()

        result_bytes = call_hf_remove_bg(resized_bytes)

        result_b64 = base64.b64encode(result_bytes).decode("utf-8")
        return jsonify({
            "success": True,
            "image": f"data:image/png;base64,{result_b64}",
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 2 — ATS CHECKER  (local spaCy NLP — lightweight, no GPU needed)
# ══════════════════════════════════════════════════════════════════════════════

TECH_SKILLS = {
    "python","javascript","typescript","java","c++","c#","go","rust",
    "react","angular","vue","node.js","express","django","flask","spring",
    "sql","mysql","postgresql","mongodb","redis","elasticsearch",
    "aws","azure","gcp","docker","kubernetes","terraform","jenkins",
    "git","linux","bash","rest","graphql","microservices",
    "machine learning","deep learning","tensorflow","pytorch","scikit-learn",
    "html","css","tailwind","figma","agile","scrum","ci/cd",
    "data analysis","power bi","tableau","excel","communication",
    "leadership","problem solving","teamwork","project management",
}

STOP_WORDS = {
    "the","and","or","of","to","a","an","in","for","with","on","at","by",
    "from","as","is","are","was","were","be","been","being","have","has",
    "had","do","does","did","will","would","could","should","may","might",
    "shall","can","not","no","but","if","then","that","this","it","its",
    "we","i","you","they","he","she","our","their","your","my","his","her",
    "also","more","other","into","through","during","before","after","about",
    "between","out","over","under","again","once","here","there","when",
    "where","why","how","all","both","each","few","more","most","some",
    "such","than","too","very","just","because","while","although","however",
}

def tokenize(text):
    """Pure Python tokenizer — splits on non-alphanumeric, removes stop words."""
    words = re.findall(r'\b[a-zA-Z][a-zA-Z0-9\+\#\.]*\b', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 2]

def extract_keywords(text):
    """Extract keywords using pure Python — no NLP library needed."""
    keywords = set()
    text_lower = text.lower()

    # Match known tech skills first (handles multi-word like "machine learning")
    for skill in TECH_SKILLS:
        if skill in text_lower:
            keywords.add(skill)

    # Extract meaningful single words
    tokens = tokenize(text)
    freq = Counter(tokens)
    # Keep words that appear at least once and are meaningful length
    for word, count in freq.items():
        if len(word) > 3:
            keywords.add(word)

    # Extract 2-word phrases (bigrams) that appear in the text
    words = re.findall(r'\b[a-z][a-z0-9]*\b', text_lower)
    for i in range(len(words) - 1):
        if words[i] not in STOP_WORDS and words[i+1] not in STOP_WORDS:
            bigram = f"{words[i]} {words[i+1]}"
            if len(bigram) > 6:
                keywords.add(bigram)

    return keywords

def tfidf_similarity(r, j):
    """Cosine similarity using pure Python TF-IDF."""
    def word_freq(text):
        words = tokenize(text)
        f = Counter(words)
        return f

    rf, jf = word_freq(r), word_freq(j)
    all_w = set(rf) | set(jf)
    dot = sum(rf.get(w, 0) * jf.get(w, 0) for w in all_w)
    mr = math.sqrt(sum(v**2 for v in rf.values()))
    mj = math.sqrt(sum(v**2 for v in jf.values()))
    return dot / (mr * mj) if mr and mj else 0.0

def calculate_ats_score(resume_text, jd_text):
    rkw = extract_keywords(resume_text)
    jkw = extract_keywords(jd_text)

    kw_score  = len(rkw & jkw) / len(jkw) if jkw else 0.5
    tf_score  = tfidf_similarity(resume_text, jd_text)

    jd_lower  = jd_text.lower()
    r_lower   = resume_text.lower()
    jd_skills = {s for s in TECH_SKILLS if s in jd_lower}
    r_skills  = {s for s in TECH_SKILLS if s in r_lower}
    sk_score  = len(r_skills & jd_skills) / len(jd_skills) if jd_skills else 1.0

    total = min(int((kw_score * 0.4 + tf_score * 0.4 + sk_score * 0.2) * 100), 99)

    missing_tech    = [s for s in jd_skills if s not in r_skills]
    missing_general = [k for k in list(jkw) if k not in rkw and k not in TECH_SKILLS
                       and len(k) > 4 and " " not in k][:10]

    return {
        "score":               total,
        "keyword_match":       round(kw_score * 100),
        "content_similarity":  round(tf_score * 100),
        "skills_coverage":     round(sk_score * 100),
        "matched_keywords":    list(rkw & jkw)[:15],
        "missing_keywords":    missing_tech[:8] + missing_general[:max(0, 12 - len(missing_tech))],
    }

def generate_suggestions(sd, resume_text, jd_text):
    s = []
    if sd["score"] < 50:
        s.append({"type":"critical","title":"Low keyword alignment","detail":"Rewrite your summary and skills section to mirror the JD language."})
    if sd["missing_keywords"]:
        s.append({"type":"warning","title":"Add missing keywords","detail":f"These appear in the JD but not your resume: {', '.join(sd['missing_keywords'][:5])}"})
    if sd["skills_coverage"] < 60:
        s.append({"type":"warning","title":"Strengthen technical skills section","detail":"The JD asks for specific technical skills that are missing."})
    if not re.search(r'\d+%|\d+x|\$\d+|\d+ year', resume_text):
        s.append({"type":"info","title":"Add measurable achievements","detail":"Add numbers: 'Reduced load time by 40%', 'Led team of 8', etc."})
    if sd["score"] >= 75:
        s.append({"type":"success","title":"Strong ATS alignment","detail":"Your resume is well-optimised. Focus on polishing your summary."})
    return s

@app.route("/api/ats-check", methods=["POST"])
def ats_check():
    try:
        data = request.get_json()
        resume = data.get("resume", "").strip()
        jd     = data.get("jobDescription", "").strip()
        if not resume or not jd:
            return jsonify({"error": "Both resume and jobDescription are required"}), 400
        sd = calculate_ats_score(resume, jd)
        return jsonify({
            "success": True,
            "score": sd["score"],
            "breakdown": {
                "keywordMatch":      sd["keyword_match"],
                "contentSimilarity": sd["content_similarity"],
                "skillsCoverage":    sd["skills_coverage"],
            },
            "matchedKeywords": sd["matched_keywords"],
            "missingKeywords": sd["missing_keywords"],
            "suggestions":     generate_suggestions(sd, resume, jd),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ══════════════════════════════════════════════════════════════════════════════
# FEATURE 3 — HEADSHOT GENERATOR
# Strategy:
#   1. Remove background via HF RMBG-1.4  (reuse same function)
#   2. Enhance the subject image with PIL  (brightness, contrast, sharpen)
#   3. Composite on chosen solid background colour
#   4. Return as JPEG
# No OpenCV / face detection model needed — PIL does the job for enhancement.
# ══════════════════════════════════════════════════════════════════════════════

BG_COLORS = {
    "linkedin":      (8,   76,  138),
    "professional":  (240, 240, 240),
    "white":         (255, 255, 255),
    "dark":          (28,  28,  40),
    "gradient_blue": None,           # handled separately
}

def enhance_and_composite(subject_png_bytes: bytes, style: str, orig_size: tuple) -> bytes:
    """Enhance subject and paste onto chosen background colour."""
    subject = Image.open(io.BytesIO(subject_png_bytes)).convert("RGBA")

    # Resize to portrait dimensions
    W, H = 500, 600
    subject = subject.resize((W, H), Image.LANCZOS)

    # Enhance with PIL
    rgb = subject.convert("RGB")
    rgb = ImageEnhance.Brightness(rgb).enhance(1.06)
    rgb = ImageEnhance.Contrast(rgb).enhance(1.12)
    rgb = ImageEnhance.Color(rgb).enhance(1.08)
    rgb = ImageEnhance.Sharpness(rgb).enhance(1.5)
    subject.paste(rgb, mask=subject.split()[3])   # keep alpha

    # Background
    if style == "gradient_blue":
        import numpy as np
        arr = np.zeros((H, W, 3), dtype=np.uint8)
        for row in range(H):
            t = row / H
            arr[row] = [int((1-t)*10+t*30), int((1-t)*60+t*100), int((1-t)*140+t*180)]
        bg = Image.fromarray(arr, "RGB").convert("RGBA")
    else:
        color = BG_COLORS.get(style, BG_COLORS["professional"])
        bg = Image.new("RGBA", (W, H), (*color, 255))

    composite = Image.alpha_composite(bg, subject)

    out = io.BytesIO()
    composite.convert("RGB").save(out, format="JPEG", quality=92, optimize=True)
    out.seek(0)
    return out.read()


@app.route("/api/headshot", methods=["POST"])
def headshot():
    try:
        data = request.get_json()
        if not data or "image" not in data:
            return jsonify({"error": "No image provided"}), 400

        raw = data["image"]
        if "," in raw:
            raw = raw.split(",", 1)[1]
        img_bytes = base64.b64decode(raw)

        style = data.get("style", "linkedin")
        if style not in BG_COLORS:
            style = "linkedin"

        # Step 1 — Resize
        pil = Image.open(io.BytesIO(img_bytes)).convert("RGB")
        orig_size = pil.size
        pil.thumbnail((1024, 1024), Image.LANCZOS)
        buf = io.BytesIO()
        pil.save(buf, format="JPEG", quality=88)
        buf.seek(0)
        resized_bytes = buf.read()

        # Step 2 — Remove background via HF
        no_bg_bytes = call_hf_remove_bg(resized_bytes)

        # Step 3 — Enhance + composite
        final_bytes = enhance_and_composite(no_bg_bytes, style, orig_size)

        result_b64 = base64.b64encode(final_bytes).decode("utf-8")
        return jsonify({
            "success": True,
            "image": f"data:image/jpeg;base64,{result_b64}",
            "style": style,
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ─── Health ───────────────────────────────────────────────────────────────────
@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "hf_token_set": bool(HF_TOKEN)})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5001))
    print(f"[CareerAI] Starting on port {port}")
    print(f"[CareerAI] HF token: {'SET' if HF_TOKEN else 'NOT SET — image features will fail'}")
    print("[CareerAI] Ready — no model preload needed.")
    app.run(host="0.0.0.0", port=port, debug=False)
