# StoryNest AI

A personalized children's story web app with an animated storybook UI, built with Flask.

## Features

- Global animated background (clouds, stars, moon, sparkles, hearts, balloons) reused across every page
- Page-specific storybook themes (home, create, library, favorites, about, contact, errors)
- Story creation form (name, age, companion animal, setting, genre, optional lesson)
- Animated "Creating your magical story..." generation overlay
- Local, dependency-free story generator (no external AI API key required)
- Story pages with a background that dynamically matches the story's setting
  (Magical Forest, Space, Underwater World, Dinosaur Land, Castle, Village, School)
- Story library, favorites, about, contact, and friendly 404 / 500 pages
- `prefers-reduced-motion` support and lighter animation on small screens
- No external animation libraries — pure CSS animations

## Setup

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Then open http://localhost:5000

## Project structure

```
storynest/
├── app.py                     # Flask routes + local story generator
├── requirements.txt
├── static/
│   ├── css/
│   │   ├── style.css          # design system (colors, type, components)
│   │   └── backgrounds.css    # animated background system
│   ├── js/
│   │   └── main.js            # nav toggle, reduced-motion/density handling
│   └── data/
│       └── stories.json       # simple JSON "database" of generated stories
└── templates/
    ├── base.html               # shared shell + global animated background
    ├── index.html               # home
    ├── create.html               # story creation form + generation overlay
    ├── story_result.html         # generated story with setting-based background
    ├── history.html               # story library
    ├── favorites.html             # favorited stories
    ├── about.html
    ├── contact.html
    ├── 404.html
    └── 500.html
```

## Connecting a real AI model (optional)

Story text is produced locally in `generate_story_text()` inside `app.py`, so the
app works out of the box with no API key. To use a real language model instead,
replace the body of that function with a call to your provider of choice, using
the same parameters (child's name, age, companion, setting, genre, lesson) to
build the prompt, and return a list of paragraph strings.
