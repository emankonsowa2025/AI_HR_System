import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict

from backend.db.db import get_connection

MAP_PATH = Path(__file__).resolve().parent.parent / "data" / "skill_job_map.json"


def _load_map() -> Dict:
    if not MAP_PATH.exists():
        return {}
    with open(MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_skills(user_id: str, skills: List[str]):
    """Persist user skills into the `skills` table (simple append)."""
    conn = get_connection()
    cur = conn.cursor()
    now = datetime.utcnow().isoformat()
    for s in skills:
        cur.execute("INSERT INTO skills (user_id, skill, created_at) VALUES (?, ?, ?)", (user_id, s.lower(), now))
    conn.commit()
    conn.close()


def get_user_skills(user_id: str) -> List[str]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT skill FROM skills WHERE user_id = ?", (user_id,))
    rows = cur.fetchall()
    conn.close()
    return [r[0] for r in rows]


def analyze_skills(skills: List[str]) -> Dict:
    """Return suggested job titles and interview questions based on skills.

    Simple heuristic: count matches against skill_job_map and rank titles.
    """
    mapping = _load_map()
    if not skills:
        return {"titles": mapping.get("default", {}).get("titles", []), "questions": mapping.get("default", {}).get("questions", [])}

    skills_norm = [s.lower() for s in skills]

    title_scores: Dict[str, int] = {}
    question_set = set()

    # Score titles by skill matches, and collect questions
    for skill in skills_norm:
        info = mapping.get(skill)
        if info:
            for t in info.get("titles", []):
                title_scores[t] = title_scores.get(t, 0) + 1
            for q in info.get("questions", []):
                question_set.add(q)

    # Fallback to default if nothing matched
    if not title_scores:
        default = mapping.get("default", {})
        return {"titles": default.get("titles", []), "questions": default.get("questions", [])}

    # sort titles by score desc
    sorted_titles = sorted(title_scores.items(), key=lambda kv: kv[1], reverse=True)
    titles = [t for t, _ in sorted_titles]

    return {"titles": titles, "questions": list(question_set)}
