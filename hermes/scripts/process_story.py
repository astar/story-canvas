#!/usr/bin/env python3
"""Autonomní storyboard generator pro Hermes.

Vezme příběh/URL/téma → Gemini CLI vygeneruje beats → kompozice
Excalidraw JSON → render PNG → uložení do Feynman vault → Telegram.

Sdílí Excalidraw layout logiku a render skript s Claude Code variantou
v ~/project/story-canvas/.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
import unicodedata
from datetime import date
from pathlib import Path

logger = logging.getLogger(__name__)

# ── Paths ──────────────────────────────────────────────────────────────────────
STORY_CANVAS_DIR = Path.home() / "project" / "story-canvas"
RENDER_SCRIPT = STORY_CANVAS_DIR / "references" / "render_excalidraw.py"
UV_BIN = Path.home() / ".local" / "bin" / "uv"
def _default_vault_visuals() -> Path:
    """Detekuje Feynman vault Visualizations adresář — Mac vs gpu1."""
    candidates = [
        Path.home() / "Obsidian" / "feynman" / "Visualizations",          # Mac
        Path.home() / "project" / "feynman-obsidian" / "Visualizations",   # gpu1
    ]
    for c in candidates:
        if c.parent.exists():
            return c
    return candidates[0]


VAULT_VISUALS = _default_vault_visuals()

# Gemini CLI
GEMINI_CANDIDATES = [
    "/usr/bin/gemini",
    str(Path.home() / ".npm-global" / "bin" / "gemini"),
    "/opt/homebrew/bin/gemini",
]
DEFAULT_CHAT_ID = "703784943"


def _find_gemini() -> str:
    for p in GEMINI_CANDIDATES:
        if Path(p).exists():
            return p
    found = shutil.which("gemini")
    if found:
        return found
    raise RuntimeError("gemini CLI nenalezeno — nainstaluj `npm install -g @google/gemini-cli`")


def _load_telegram_token() -> str | None:
    if "TELEGRAM_BOT_TOKEN" in os.environ:
        return os.environ["TELEGRAM_BOT_TOKEN"]
    env_file = Path.home() / ".hermes" / ".env"
    if env_file.exists():
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip("\"'")
    return None


# ── Color & layout constants ──────────────────────────────────────────────────
COLOR_MAP = {
    "setup":      {"stroke": "#92400e", "background": "#fef3c7"},  # yellow
    "conflict":   {"stroke": "#991b1b", "background": "#fee2e2"},  # red
    "insight":    {"stroke": "#1e40af", "background": "#dbeafe"},  # blue
    "resolution": {"stroke": "#065f46", "background": "#d1fae5"},  # green
    "mentor":     {"stroke": "#6d28d9", "background": "#ede9fe"},  # purple
}

CONNECTOR_COLOR = {
    "Additive":  "#475569",
    "Causal":    "#1e40af",
    "Pivot":     "#991b1b",
    "Reversal":  "#991b1b",
    "Loop":      "#6d28d9",
}

# Map common connector words to category (for coloring)
CONNECTOR_CATEGORY = {
    "and": "Additive", "also": "Additive", "then": "Additive", "furthermore": "Additive",
    "therefore": "Causal", "because": "Causal", "so": "Causal", "thus": "Causal",
    "but": "Pivot", "yet": "Pivot", "still": "Pivot", "though": "Pivot",
    "however": "Reversal", "nevertheless": "Reversal", "despite this": "Reversal",
    "ironically": "Loop", "paradoxically": "Loop", "ultimately": "Loop",
    "as it turns out": "Loop",
}


# ── Slug ───────────────────────────────────────────────────────────────────────
def slugify(text: str, max_len: int = 50) -> str:
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text[:max_len].rstrip("-") or "story"


# ── Input fetching ─────────────────────────────────────────────────────────────
def fetch_text(source: str) -> str:
    """Vrátí čistý markdown text — URL → markdownify, soubor → read, jinak vrátí source."""
    if source.startswith("http://") or source.startswith("https://"):
        try:
            from bs4 import BeautifulSoup
            from markdownify import markdownify as md
        except ImportError:
            # fallback: stažení raw HTML s minimální transformací
            req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=30) as r:
                html = r.read().decode("utf-8", errors="replace")
            return re.sub(r"<[^>]+>", " ", html)
        req = urllib.request.Request(source, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            html = r.read().decode("utf-8", errors="replace")
        soup = BeautifulSoup(html, "html.parser")
        article = soup.find("article") or soup.find("main") or soup.body
        return md(str(article), heading_style="ATX") if article else md(html, heading_style="ATX")
    p = Path(source)
    if p.exists() and p.is_file():
        return p.read_text(encoding="utf-8")
    return source  # raw text


# ── Gemini call ────────────────────────────────────────────────────────────────
GEMINI_PROMPT_TEMPLATE = """\
Jsi expertní vizuální vypravěč. Dostaneš text/příběh/téma a tvým úkolem je
vytvořit storyboard ve formátu JSON, který se použije pro Excalidraw sticky-note
canvas.

FRAMEWORK: {framework}
{framework_instructions}

PRAVIDLA:
- Identifikuj 5-9 hlavních beats (klíčových bodů příběhu)
- Pro každý beat napiš 3-7 slov krátký label (musí se vejít na sticky note)
- Mezi beats zvol connector slova z této tabulky:
  Additive (slabé): And, Also, Then, Furthermore
  Causal (kauzalita): Therefore, Because, So, Thus, As a result
  Pivot (kontrast): But, Yet, Still, Though, However
  Reversal (obrat): However, Nevertheless, In contrast, Despite this
  Loop (pointa): Ironically, Paradoxically, As it turns out, Ultimately
  Preferuj kontrast a kauzalitu, vyhni se monotónnímu "and/then".
- Přiřaď každému beatu category: setup, conflict, insight, resolution, mentor.

VRAŤ POUZE JSON V TOMTO FORMÁTU (žádný jiný text, žádný markdown fence):

{{
  "title_cs": "Krátký český titulek příběhu (max 80 znaků)",
  "subtitle_cs": "Volitelný podtitulek (1 věta)",
  "tagline": "Volitelná tagline na konci canvasu (krátká věta)",
  "framework": "{framework}",
  "beats": [
    {{"label": "Text beatu na sticky note (krátký, 3-10 slov)", "category": "setup", "emoji": "🏹"}},
    {{"label": "Další beat", "category": "conflict", "emoji": "⚖️"}}
  ],
  "connectors": ["But", "Therefore", "Yet", "Ironically"]
}}

POZNÁMKA: počet connectors = počet beats - 1.

TEXT/PŘÍBĚH/TÉMA:

{input_text}
"""

FRAMEWORK_INSTRUCTIONS = {
    "south-park": (
        "Stone/Parker pravidlo — scény propojené but/therefore (kauzalita, "
        "kontrast, paradoxy). 5-9 beats v lineární sekvenci."
    ),
    "pixar": (
        "Pixar Story Spine — přesně 6 beats: 1) Once upon a time, 2) Every day, "
        "3) Until one day, 4) Because of that, 5) Because of that, 6) Until finally."
    ),
    "hero-journey": (
        "Joseph Campbell Hero's Journey — 8-12 stages: Ordinary World, Call to "
        "Adventure, Refusal, Mentor, Threshold, Tests, Ordeal, Reward, Return."
    ),
    "save-the-cat": (
        "Blake Snyder Save the Cat — 10-15 beats: Opening, Theme Stated, Setup, "
        "Catalyst, Debate, Break into Two, Midpoint, All Is Lost, Finale, Final Image."
    ),
}


def call_gemini(prompt: str, *, timeout: int = 180) -> str:
    binary = _find_gemini()
    env = {**os.environ, "HOME": str(Path.home())}
    result = subprocess.run(
        [binary, "-p", prompt, "-y", "--output-format", "json"],
        input=b"",
        capture_output=True,
        timeout=timeout,
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(f"gemini exit {result.returncode}: {result.stderr.decode()[-300:]}")
    try:
        data = json.loads(result.stdout.decode())
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"gemini nevalidní JSON: {result.stdout.decode()[:200]}") from exc
    return data.get("response", "")


def parse_json_response(text: str) -> dict:
    fence = re.search(r"```(?:json)?\s*\n(.*?)\n```", text, re.DOTALL)
    if fence:
        text = fence.group(1)
    text = text.strip()
    return json.loads(text)


# ── Excalidraw composition ─────────────────────────────────────────────────────
CARD_W, CARD_H = 280, 150
GAP_X = 70
ROW_Y = [200, 500]


def compose_excalidraw(spec: dict) -> dict:
    """Z parsovaného Gemini outputu vytvoří Excalidraw JSON."""
    beats = spec["beats"]
    connectors = spec.get("connectors") or ["But"] * (len(beats) - 1)
    title = spec.get("title_cs", "Story canvas")
    subtitle = spec.get("subtitle_cs", "")
    tagline = spec.get("tagline", "")

    n = len(beats)
    # Snake layout: row 1 LTR, row 2 RTL.
    per_row = 4 if n > 4 else n
    positions: list[tuple[int, int, int]] = []  # (row, col_in_row, direction)
    for i in range(n):
        row = i // per_row
        col = i % per_row
        if row % 2 == 1:
            # reverse row direction
            col = per_row - 1 - col
        positions.append((row, col, 1 if row % 2 == 0 else -1))

    elements: list[dict] = []

    # Title (top)
    elements.append({
        "id": "title-main", "type": "text",
        "x": 100, "y": 80, "width": 1330, "height": 50,
        "text": title, "fontFamily": 1, "fontSize": 30,
        "textAlign": "left", "verticalAlign": "top",
        "strokeColor": "#1e293b",
    })
    if subtitle:
        elements.append({
            "id": "title-sub", "type": "text",
            "x": 100, "y": 135, "width": 1330, "height": 30,
            "text": subtitle, "fontFamily": 1, "fontSize": 18,
            "textAlign": "left", "verticalAlign": "top",
            "strokeColor": "#475569",
        })

    # Cards + labels
    for i, beat in enumerate(beats):
        row, col, _ = positions[i]
        x = 100 + col * (CARD_W + GAP_X)
        y = ROW_Y[row]
        color = COLOR_MAP.get(beat.get("category", "setup"), COLOR_MAP["setup"])
        elements.append({
            "id": f"card-{i+1}", "type": "rectangle",
            "x": x, "y": y, "width": CARD_W, "height": CARD_H,
            "strokeColor": color["stroke"], "backgroundColor": color["background"],
            "fillStyle": "solid", "strokeWidth": 2,
            "roundness": {"type": 3}, "roughness": 1,
        })
        label_text = beat.get("label", "")
        emoji = beat.get("emoji", "")
        text_content = f"{emoji}\n\n{label_text}" if emoji else label_text
        elements.append({
            "id": f"label-{i+1}", "type": "text",
            "x": x + 10, "y": y + 20, "width": CARD_W - 20, "height": CARD_H - 40,
            "text": text_content, "fontFamily": 1, "fontSize": 18,
            "textAlign": "center", "verticalAlign": "middle",
            "strokeColor": "#1e293b",
        })

    # Arrows + connector labels
    for i in range(n - 1):
        src_row, src_col, _ = positions[i]
        dst_row, dst_col, _ = positions[i + 1]
        src_x = 100 + src_col * (CARD_W + GAP_X)
        src_y = ROW_Y[src_row]
        dst_x = 100 + dst_col * (CARD_W + GAP_X)
        dst_y = ROW_Y[dst_row]
        connector_word = connectors[i] if i < len(connectors) else "Then"
        category = CONNECTOR_CATEGORY.get(connector_word.lower(), "Causal")
        color = CONNECTOR_COLOR.get(category, "#475569")

        if src_row == dst_row:
            # Horizontal arrow
            if dst_col > src_col:
                ax, ay, aw, points = src_x + CARD_W, src_y + CARD_H // 2, GAP_X, [[0, 0], [GAP_X, 0]]
            else:
                ax, ay, aw, points = src_x - GAP_X, src_y + CARD_H // 2, GAP_X, [[GAP_X, 0], [0, 0]]
            elements.append({
                "id": f"arrow-{i+1}-{i+2}", "type": "arrow",
                "x": ax, "y": ay, "width": aw, "height": 0,
                "points": points,
                "startBinding": {"elementId": f"card-{i+1}", "focus": 0, "gap": 5},
                "endBinding": {"elementId": f"card-{i+2}", "focus": 0, "gap": 5},
                "strokeColor": "#1e293b", "strokeWidth": 2,
                "endArrowhead": "arrow", "roughness": 1,
            })
            # Connector label centered above
            label_w = max(50, len(connector_word) * 9)
            label_x = ax + aw // 2 - label_w // 2
            label_y = ay - 30
            elements.append({
                "id": f"conn-{i+1}-{i+2}", "type": "text",
                "x": label_x, "y": label_y, "width": label_w, "height": 22,
                "text": connector_word, "fontFamily": 1, "fontSize": 14,
                "textAlign": "center", "strokeColor": color,
            })
        else:
            # Vertical arrow (row break)
            mid_x = src_x + CARD_W // 2
            ax, ay = mid_x, src_y + CARD_H
            elements.append({
                "id": f"arrow-{i+1}-{i+2}", "type": "arrow",
                "x": ax, "y": ay, "width": 0, "height": dst_y - ay,
                "points": [[0, 0], [0, dst_y - ay]],
                "startBinding": {"elementId": f"card-{i+1}", "focus": 0, "gap": 5},
                "endBinding": {"elementId": f"card-{i+2}", "focus": 0, "gap": 5},
                "strokeColor": "#1e293b", "strokeWidth": 2,
                "endArrowhead": "arrow", "roughness": 1,
            })
            elements.append({
                "id": f"conn-{i+1}-{i+2}", "type": "text",
                "x": ax + 10, "y": ay + (dst_y - ay) // 2 - 10,
                "width": max(60, len(connector_word) * 9), "height": 22,
                "text": connector_word, "fontFamily": 1, "fontSize": 14,
                "textAlign": "left", "strokeColor": color,
            })

    # Tagline (bottom)
    if tagline:
        max_y = max(ROW_Y[row] for row, _, _ in positions) + CARD_H
        elements.append({
            "id": "tagline", "type": "text",
            "x": 100, "y": max_y + 30, "width": 1330, "height": 30,
            "text": f"„{tagline}\"", "fontFamily": 1, "fontSize": 20,
            "textAlign": "center", "verticalAlign": "top",
            "strokeColor": "#475569",
        })

    return {
        "type": "excalidraw", "version": 2, "source": "https://excalidraw.com",
        "elements": elements,
        "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
        "files": {},
    }


# ── Render ─────────────────────────────────────────────────────────────────────
def render_to_png(excalidraw_path: Path, png_path: Path) -> Path:
    cmd = [
        str(UV_BIN), "run", "--project", str(STORY_CANVAS_DIR / "references"),
        "python", str(RENDER_SCRIPT),
        str(excalidraw_path),
        "--output", str(png_path),
        "--scale", "2", "--width", "1920",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        raise RuntimeError(f"render selhal: {result.stderr[-300:]}")
    return png_path


# ── Telegram ───────────────────────────────────────────────────────────────────
def send_telegram_photo(photo_path: Path, caption: str, chat_id: str) -> bool:
    token = _load_telegram_token()
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN nenalezen — přeskakuju Telegram.")
        return False
    boundary = "----storyCanvasBoundary"
    crlf = "\r\n"
    parts: list[bytes] = []
    for k, v in {"chat_id": chat_id, "caption": caption[:1000], "parse_mode": "Markdown"}.items():
        parts.append(
            (f"--{boundary}{crlf}"
             f'Content-Disposition: form-data; name="{k}"{crlf}{crlf}'
             f"{v}{crlf}").encode("utf-8")
        )
    file_bytes = photo_path.read_bytes()
    parts.append(
        (f"--{boundary}{crlf}"
         f'Content-Disposition: form-data; name="photo"; filename="{photo_path.name}"{crlf}'
         f"Content-Type: image/png{crlf}{crlf}").encode("utf-8") + file_bytes + crlf.encode("utf-8")
    )
    parts.append(f"--{boundary}--{crlf}".encode("utf-8"))
    body = b"".join(parts)
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{token}/sendPhoto",
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    return bool(data.get("ok"))


# ── Main ──────────────────────────────────────────────────────────────────────
def process(
    source: str,
    *,
    framework: str = "south-park",
    title_override: str | None = None,
    slug_override: str | None = None,
    skip_telegram: bool = False,
    chat_id: str = DEFAULT_CHAT_ID,
    output_dir: Path = VAULT_VISUALS,
) -> dict:
    logger.info("=== STEP 1: fetch ===")
    input_text = fetch_text(source)
    if title_override:
        input_text = f"{title_override}\n\n{input_text}"
    logger.info("Input text length: %d chars", len(input_text))

    logger.info("=== STEP 2: Gemini generate beats ===")
    prompt = GEMINI_PROMPT_TEMPLATE.format(
        framework=framework,
        framework_instructions=FRAMEWORK_INSTRUCTIONS.get(framework, FRAMEWORK_INSTRUCTIONS["south-park"]),
        input_text=input_text[:8000],
    )
    response = call_gemini(prompt)
    spec = parse_json_response(response)

    logger.info("=== STEP 3: compose Excalidraw JSON ===")
    excalidraw = compose_excalidraw(spec)

    logger.info("=== STEP 4: save files ===")
    output_dir.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    slug = slug_override or slugify(title_override or spec.get("title_cs", "story"))
    stem = f"{today}-{slug}"
    excal_path = output_dir / f"{stem}.excalidraw"
    png_path = output_dir / f"{stem}.png"

    excal_path.write_text(
        json.dumps(excalidraw, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    logger.info("=== STEP 5: render PNG ===")
    render_to_png(excal_path, png_path)

    logger.info("=== STEP 6: Telegram ===")
    if not skip_telegram:
        caption_lines = [f"📖 *{spec.get('title_cs','Story')}*"]
        if spec.get("subtitle_cs"):
            caption_lines.append(f"_{spec['subtitle_cs']}_")
        caption_lines.append("")
        caption_lines.append(f"Framework: `{framework}` · {len(spec['beats'])} beats")
        for i, beat in enumerate(spec["beats"], 1):
            cat = beat.get("category", "")
            caption_lines.append(f"{i}. [{cat}] {beat.get('label','')}")
        try:
            send_telegram_photo(png_path, "\n".join(caption_lines), chat_id)
        except Exception as exc:
            logger.warning("Telegram selhal: %s", exc)

    return {"excalidraw": str(excal_path), "png": str(png_path), "spec": spec}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("source", help="text příběhu / URL / cesta k souboru")
    ap.add_argument(
        "--framework",
        choices=["south-park", "pixar", "hero-journey", "save-the-cat"],
        default="south-park",
    )
    ap.add_argument("--title", default=None, help="přepiš titulek")
    ap.add_argument("--slug", default=None, help="přepiš slug (filename stem)")
    ap.add_argument("--output-dir", type=Path, default=VAULT_VISUALS)
    ap.add_argument("--skip-telegram", action="store_true")
    ap.add_argument("--telegram-target", default=DEFAULT_CHAT_ID)
    args = ap.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        result = process(
            args.source,
            framework=args.framework,
            title_override=args.title,
            slug_override=args.slug,
            skip_telegram=args.skip_telegram,
            chat_id=args.telegram_target,
            output_dir=args.output_dir,
        )
    except Exception as exc:
        logger.exception("Story canvas selhal: %s", exc)
        return 1
    print(f"OK")
    print(f"  excalidraw: {result['excalidraw']}")
    print(f"  png:        {result['png']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
