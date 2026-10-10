"""
StoryNest AI — Flask application
A personalized children's story generator with an animated storybook UI.

Runs completely standalone: story text is produced by a local, rule-based
generator (see `generate_story_text`) so no external AI/image API key is
required. Swap `generate_story_text` for a real LLM call if you have one
available (see the comment near that function for where to plug it in).
"""

import json
import os
import re
import uuid
import random
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, jsonify

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False

DATA_FILE = os.path.join(os.path.dirname(__file__), "static", "data", "stories.json")

# ---------------------------------------------------------------------------
# Storage helpers (simple JSON file — swap for a real database in production)
# ---------------------------------------------------------------------------

def _load_stories():
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return []


def _save_stories(stories):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(stories, f, indent=2, ensure_ascii=False)


def get_story(story_id):
    for s in _load_stories():
        if s["id"] == story_id:
            return s
    return None


# ---------------------------------------------------------------------------
# Setting → visual theme mapping
# ---------------------------------------------------------------------------

SETTING_THEME = {
    "Magical Forest":    {"bg_class": "forest-bg",     "color_a": "#2F6B45", "color_b": "#12261C"},
    "Space":             {"bg_class": "space-bg",      "color_a": "#181430", "color_b": "#4A3F8C"},
    "Underwater World":  {"bg_class": "underwater-bg", "color_a": "#0E3A52", "color_b": "#0A2438"},
    "Dinosaur Land":     {"bg_class": "dinosaur-bg",   "color_a": "#8a6a00", "color_b": "#3D3319"},
    "Castle":            {"bg_class": "castle-bg",     "color_a": "#3A1F4A", "color_b": "#7C4A9C"},
    "Village":           {"bg_class": "village-bg",    "color_a": "#B98A2E", "color_b": "#3D3319"},
    "School":            {"bg_class": "school-bg",     "color_a": "#1F2E4A", "color_b": "#3E5A9C"},
}
DEFAULT_THEME = {"bg_class": "magical-bg", "color_a": "#4A3F8C", "color_b": "#2E2A5C"}

VALID_SETTINGS = list(SETTING_THEME.keys())
VALID_GENRES = ["Adventure", "Friendship", "Mystery", "Bedtime", "Silly & Fun"]
VALID_COMPANIONS = ["Fox", "Rabbit", "Dragon", "Owl", "Unicorn", "Puppy"]


# ---------------------------------------------------------------------------
# Story generation (local, rule-based — no external API required)
# ---------------------------------------------------------------------------

SETTING_FLAVOR = {
    "Magical Forest": {
        "place": "a forest where the mushrooms glowed like little lanterns",
        "detail": "fireflies drifted between the trees, blinking in lazy little patterns",
        "obstacle": "a puzzle of tangled vines guarding an old stone archway",
        "wonder": "a clearing where the flowers hummed a soft, sleepy tune",
    },
    "Space": {
        "place": "a small silver rocket drifting past rings of candy-colored dust",
        "detail": "the stars blinked hello, one after another, like a string of fairy lights",
        "obstacle": "an asteroid field shaped like a maze of floating stepping stones",
        "wonder": "a quiet moon where the ground bounced like a trampoline",
    },
    "Underwater World": {
        "place": "a coral kingdom where the water sparkled like liquid glass",
        "detail": "schools of rainbow fish swirled by in ribbons of color",
        "obstacle": "a curtain of swaying kelp hiding a narrow, winding path",
        "wonder": "a cave lit from within by softly glowing pearls",
    },
    "Dinosaur Land": {
        "place": "a warm valley where gentle giants grazed beneath tall ferns",
        "detail": "the ground gave a friendly little rumble with every distant footstep",
        "obstacle": "a wide river crossed only by a row of very patient turtles",
        "wonder": "a hillside of eggs just beginning to wobble and crack",
    },
    "Castle": {
        "place": "a castle with towers that seemed to brush the clouds",
        "detail": "banners fluttered from every window in bright, cheerful colors",
        "obstacle": "a drawbridge riddle that only a kind heart could solve",
        "wonder": "a hall where the portraits waved back if you smiled first",
    },
    "Village": {
        "place": "a village of cozy cottages with flower boxes on every sill",
        "detail": "the smell of fresh bread drifted from the little bakery on the corner",
        "obstacle": "a market square puzzle set by the friendly baker",
        "wonder": "a hidden garden behind the old well, blooming out of season",
    },
    "School": {
        "place": "a school where the chalkboards sometimes doodled back",
        "detail": "pencils rolled themselves back onto desks, humming little tunes",
        "obstacle": "a locked supply closet guarded by a riddle on a sticky note",
        "wonder": "a library corner where the books whispered the best stories first",
    },
}

LESSON_LINES = {
    "sharing": "shared it without being asked, because some things are better in two",
    "courage": "took a deep breath and took the very next step anyway",
    "kindness": "stopped to help, even though nobody was watching",
    "patience": "waited quietly, trusting that good things take a little time",
    "honesty": "told the truth, even when a small fib would have been easier",
    "teamwork": "asked for help, and found the puzzle was easier with two sets of hands",
}


def _pick_lesson_line(lesson):
    if not lesson:
        return None
    lesson_key = lesson.strip().lower()
    for key, line in LESSON_LINES.items():
        if key in lesson_key:
            return line
    return f"remembered what it means to show {lesson.strip()}, and it made all the difference"


def generate_story_text(child_name, age, companion, setting, genre, lesson):
    """
    Produces a short, structured children's story.

    This is a local template-based generator so the app works with zero
    external dependencies. To use a real AI model instead, replace the body
    of this function with a call to your provider of choice (for example,
    the Anthropic Messages API) using a prompt built from these same
    parameters, and return a list of paragraph strings.
    """
    flavor = SETTING_FLAVOR.get(setting, SETTING_FLAVOR["Magical Forest"])
    lesson_line = _pick_lesson_line(lesson)

    opener_by_genre = {
        "Adventure": f"{child_name} had always dreamed of an adventure, and today, without any warning, one arrived.",
        "Friendship": f"{child_name} wasn't looking for a friend that day — but the best ones are often found by accident.",
        "Mystery": f"{child_name} noticed it first: something was not quite where it should be.",
        "Bedtime": f"As the stars came out one by one, {child_name} closed their eyes and drifted somewhere wonderful.",
        "Silly & Fun": f"It started, as the silliest days often do, with a very ordinary Tuesday for {child_name}.",
    }

    p1 = opener_by_genre.get(genre, opener_by_genre["Adventure"])
    p1 += f" A path appeared — soft, glowing, and impossible to ignore — leading straight into {flavor['place']}."

    p2 = (
        f"There, waiting with a curious tilt of the head, stood a {companion.lower()} who introduced "
        f"{'itself' if companion in ('Dragon','Unicorn') else 'themselves'} with a friendly little bow. "
        f"\"I've been hoping someone brave would come along,\" said the {companion.lower()}. "
        f"Together they walked further in, and {flavor['detail']}."
    )

    p3 = (
        f"Before long, {child_name} and the {companion.lower()} came across {flavor['obstacle']}. "
        f"It looked tricky at first, but {child_name} thought carefully, tried a gentle idea, and — "
        f"little by little — it worked. The {companion.lower()} cheered so loudly that a family of birds "
        f"scattered into the sky, laughing along."
    )

    if lesson_line:
        p4 = f"Later, when the {companion.lower()} offered {child_name} the last of a small treasure they'd found, {child_name} {lesson_line}."
    else:
        p4 = (
            f"As the light turned golden, they wandered into {flavor['wonder']}, and for a moment, "
            f"neither of them said a word — some things are best simply enjoyed."
        )

    p5 = (
        f"When it was finally time to say goodbye, the {companion.lower()} promised this was only the "
        f"beginning. \"Come back anytime,\" they said, \"the story is never really finished.\" "
        f"And with that, {child_name} smiled, feeling just a little bit braver than before."
    )

    return [p1, p2, p3, p4, p5]


def build_title(child_name, setting, genre):
    templates = [
        f"{child_name}'s Magical Adventure",
        f"{child_name} and the Secret of {setting}",
        f"The {genre} of {child_name}",
        f"{child_name}'s Journey Through {setting}",
    ]
    return random.choice(templates)


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _clean_name(raw):
    name = re.sub(r"[^A-Za-z' -]", "", (raw or "")).strip()
    return name[:40] if name else "Alex"


def _clean_choice(raw, valid_list, default):
    return raw if raw in valid_list else default


def _clean_age(raw):
    try:
        age = int(raw)
    except (TypeError, ValueError):
        return 6
    return max(2, min(12, age))


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.context_processor
def inject_globals():
    return {"current_year": datetime.utcnow().year}


@app.route("/")
def home():
    return render_template("index.html")


@app.route("/create")
def create():
    return render_template("create.html")


@app.route("/generate", methods=["POST"])
def generate():
    child_name = _clean_name(request.form.get("child_name"))
    age = _clean_age(request.form.get("age"))
    companion = _clean_choice(request.form.get("companion"), VALID_COMPANIONS, "Fox")
    setting = _clean_choice(request.form.get("setting"), VALID_SETTINGS, "Magical Forest")
    genre = _clean_choice(request.form.get("genre"), VALID_GENRES, "Adventure")
    lesson = (request.form.get("lesson") or "").strip()[:60]

    paragraphs = generate_story_text(child_name, age, companion, setting, genre, lesson)
    theme = SETTING_THEME.get(setting, DEFAULT_THEME)

    story = {
        "id": uuid.uuid4().hex[:10],
        "title": build_title(child_name, setting, genre),
        "child_name": child_name,
        "age": age,
        "companion": companion,
        "setting": setting,
        "genre": genre,
        "lesson": lesson,
        "paragraphs": paragraphs,
        "bg_class": theme["bg_class"],
        "color_a": theme["color_a"],
        "color_b": theme["color_b"],
        "favorite": False,
        "created_at": datetime.utcnow().isoformat(),
    }

    stories = _load_stories()
    stories.insert(0, story)
    _save_stories(stories)

    return jsonify({"redirect": url_for("story_detail", story_id=story["id"])})


@app.route("/story/<story_id>")
def story_detail(story_id):
    story = get_story(story_id)
    if not story:
        return render_template("404.html"), 404
    return render_template("story_result.html", story=story)


@app.route("/story/<story_id>/favorite", methods=["POST"])
def toggle_favorite(story_id):
    stories = _load_stories()
    found = False
    for s in stories:
        if s["id"] == story_id:
            s["favorite"] = not s.get("favorite", False)
            found = True
            break
    if not found:
        return render_template("404.html"), 404
    _save_stories(stories)
    return redirect(url_for("story_detail", story_id=story_id))


@app.route("/history")
def history():
    stories = _load_stories()
    return render_template("history.html", stories=stories)


@app.route("/favorites")
def favorites():
    stories = [s for s in _load_stories() if s.get("favorite")]
    return render_template("favorites.html", stories=stories)


@app.route("/about")
def about():
    return render_template("about.html")


@app.route("/contact", methods=["GET", "POST"])
def contact():
    submitted = False
    if request.method == "POST":
        # In production, send an email or store the message; kept simple here.
        submitted = True
    return render_template("contact.html", submitted=submitted)


# ---------------------------------------------------------------------------
# Error handlers — never leak tracebacks or internal details
# ---------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(e):
    return render_template("404.html"), 404


@app.errorhandler(500)
def server_error(e):
    return render_template("500.html"), 500


if __name__ == "__main__":
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    app.run(debug=True, host="0.0.0.0", port=5000)
