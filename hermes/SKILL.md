---
name: story-canvas
description: Autonomní storyboard generator pro Hermes — vezme text/URL/téma a vyrenderuje sticky-note Excalidraw canvas (South Park / Pixar / Hero's Journey / Save the Cat). Beats generuje Gemini CLI lokálně. Output do ~/project/feynman-obsidian/Visualizations/ + Telegram.
version: 1.0.0
---

# Story Canvas (Hermes variant)

## When to activate (NO confirmation needed)

Run **immediately and silently** when:

- User pošle text + slovo "storyboard", "story canvas", "vizualizuj jako příběh", "rozcvič příběh"
- User pošle URL (drwilliamwallace.com, blog, article) + "storyboard"
- User řekne "rozkresli X South Park metodou" / "udělej Hero's Journey z toho"

## Run

```bash
python3 ~/.hermes/skills/story-canvas/scripts/process_story.py "STORY_OR_URL" \
    [--framework south-park|pixar|hero-journey|save-the-cat] \
    [--style stickies|beats|arc] \
    [--title "Volitelný titulek"] \
    [--telegram-target 703784943]
```

## Pipeline

1. **Parse** input — text / URL / file path. URL → fetch + markdownify.
2. **Gemini CLI** strukturovaný prompt → JSON `{title, framework, beats[]}`.
3. **Compose** Excalidraw JSON (sticky notes, connector labels, colors).
4. **Render** PNG přes `~/project/story-canvas/references/render_excalidraw.py`.
5. **Save** do `~/project/feynman-obsidian/Visualizations/YYYY-MM-DD-<slug>.{excalidraw,png}`.
6. **Telegram** — pošle PNG s caption (titulek + framework + beats list).

## Default

- Framework: South Park (sticky-note storyboard, but/therefore connectors)
- Style: sticky notes
- Output: `.excalidraw` + `.png` (vždy oba)
- Telegram: chat 703784943

## Dependencies

- Python 3.11+ (system)
- Gemini CLI (`/usr/bin/gemini` nebo `~/.npm-global/bin/gemini`)
- `~/project/story-canvas/references/.venv/` (uv-managed, contains Playwright + Chromium)
- `~/.hermes/.env` s `TELEGRAM_BOT_TOKEN`

## Reference

Sdílí render skript s Claude Code / Gemini CLI verzí v `~/project/story-canvas/`. Tento Hermes wrapper přidává jen autonomní Gemini call pro generování beats.
