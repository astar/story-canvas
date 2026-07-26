---
name: story-canvas
description: Vytvoří Excalidraw vizualizaci příběhu, článku nebo zadání — sticky-note storyboard ve stylu Zsolt / South Park, nebo jiný framework (Pixar story spine, Hero's Journey, Save the Cat). Default sticky notes s but/therefore connectors. Renderuje .excalidraw + .png, ukládá do Feynman vault. Self-review: po render se podívá na PNG a opraví problémy. Triggery — "udělej storyboard z toho", "vizualizuj ten příběh", "story canvas", "rozkresli mi to jako příběh", URL článku + "udělej z toho příběh", "rozcvič South Park metodou".
---

# Story Canvas — visualizace příběhu jako Excalidraw

Tenhle skill bere **příběh, článek, zadání nebo téma**, rozseká ho na *beats* a vyrenderuje jako **sticky-note storyboard** v Excalidraw — propojený connector words (Yet, Therefore, But, However, Ironically). Inspirace: Zsoltova "Visual Thinking" + Matt Stone / Trey Parker storytelling secret.

## Když skill triggernout (bez ptaní)

- Uživatel pošle příběh, článek (text nebo URL) a chce vizualizaci
- Slova: "storyboard", "rozcvič příběh", "rozkresli to", "vizualizuj jako příběh", "story canvas", "udělej obrázek z článku", "but/therefore"
- URL z `drwilliamwallace.com/notes/...` + slovo "vizualizuj/storyboard" → vezmi Wallaceův článek a uděláme storyboard

Neptej se "chceš to udělat?" — spusť.

## Klíčové principy

1. **Default = South Park sticky notes** (5-9 beats, propojené but/therefore/yet). Funguje pro 90 % příběhů.
2. **Skill zná všechny frameworky** níže a sám zvolí nejvhodnější podle typu inputu (viz "Auto-volba"). Pokud uživatel jmenoval konkrétní framework, použij jeho.
3. **Output = `.excalidraw` (editovatelný v Obsidian) + `.png` (preview)** — vždycky oba.
4. **Self-review po render**: po vytvoření PNG ho **přečti tool `Read`em** a zkontroluj — překrývání textu, chybějící labels, špatně směrované šipky, nečitelnost. Pokud spotřebuje něco zjevně zlomené, regeneruj JSON a re-render (1× max v rámci default flow).
5. **Reakce na feedback uživatele**: pokud po výstupu uživatel řekne "změň X" / "líbí se mi víc Y" → uprav JSON, re-render. Nechraň ego, prostě přepiš.

## Frameworky (skill je všechny zná)

### 1. South Park — but/therefore (DEFAULT pro většinu textů)

Stone/Parker pravidlo: scény spojené "but/therefore", ne "and/then".
Použij když: článek/příběh má kauzalitu, obraty, paradoxy. Většina evidence-review textů, op-edů, biografií, novinových článků.

5 typů connectorů (vždy zvol ten nejpřesnější):

| Typ | Slova | Kdy |
|---|---|---|
| Additive | And, Also, Then, Furthermore | nudné — vyhni se, používej jen pro setup |
| **Causal** | Therefore, Because, So, Thus, As a result | **silný spoj** — A vede k B |
| **Pivot** | But, Yet, Still, Though, However | **kontrast / problém** |
| **Reversal** | However, Nevertheless, In contrast, Despite this | obrat kursem |
| **Loop** | Ironically, Paradoxically, As it turns out, Ultimately | pointa / pozdní zjištění |

Mix = krásný story rhythm. Často: Setup (Additive) → Therefore → But → Therefore → But → Ironically.

### 2. Pixar Story Spine — 6 vět

Pro: jednoduché lineární vyprávění s jedním hrdinou.

```
Once upon a time… [protagonist + ordinary world]
Every day… [normal state]
Until one day… [inciting incident]
Because of that… [consequence 1]
Because of that… [consequence 2]
Until finally… [climax + resolution]
```

Visual: 6 karet horizontálně, šipky → mezi nimi.

### 3. Hero's Journey (Joseph Campbell) — 12 stages

Pro: mýtické/dlouhé příběhy, transformační arch, biografie ("X to Y").

Stages (mohou se sloučit nebo vynechat): Ordinary World → Call to Adventure → Refusal of the Call → Meeting the Mentor → Crossing the Threshold → Tests/Allies/Enemies → Approach to Inmost Cave → Ordeal → Reward → The Road Back → Resurrection → Return with the Elixir.

Visual: kruhový diagram (12 segmentů) nebo horizontální časová osa.

### 4. Save the Cat (Blake Snyder) — 15 beats

Pro: filmové scénáře nebo strukturované long-form storytelling.

Beats: Opening Image · Theme Stated · Set-up · Catalyst · Debate · Break into Two · B Story · Fun and Games · Midpoint · Bad Guys Close In · All Is Lost · Dark Night of the Soul · Break into Three · Finale · Final Image.

Visual: horizontální beat sheet s % markery (Opening 1%, Catalyst 12%, Midpoint 50%, All Is Lost 75%, Finale 90%).

## Vizuální styly (skill je všechny zná)

### Sticky notes (DEFAULT, pro South Park i Pixar)

- Každý beat = post-it karta (rectangle, rounded, barevné pozadí)
- Šipky mezi kartami se text-label connectorem ("Yet", "Therefore", …)
- Pisátkový font (`"fontFamily": "1"` = Virgil ze sady Excalidraw — handwritten)
- Ikonky (text emoji nebo malé kruhy) v rohu pro typ beatu
- Barvy karet (palette):
  - Setup/normal: `#fef3c7` background, `#92400e` stroke (yellow)
  - Conflict/problém: `#fee2e2` background, `#991b1b` stroke (red)
  - Insight/twist: `#dbeafe` background, `#1e40af` stroke (blue)
  - Resolution/payoff: `#d1fae5` background, `#065f46` stroke (green)
  - Mentor/wisdom: `#ede9fe` background, `#6d28d9` stroke (purple)

### Beat sheet — horizontální časová osa

Pro Save the Cat: horizontální čára s ticks na % pozicích, beats jako bubliny nad/pod čárou.

### Hero's circle / arc

Pro Hero's Journey: kruh rozdělený na 12 segmentů (jako hodinky) nebo Freytagův obloukový graf (vzestup → vrchol → sestup).

### Mountain / arc

Pro fryagův dramatický oblouk: setup base → rising line → peak (climax) → falling line → resolution base.

## Auto-volba frameworku & stylu

Pokud uživatel **explicitně nepojmenoval** framework, rozhodni:

1. **Text < 500 slov, blog post, article** → South Park sticky notes (default)
2. **"Biografie X", "cesta od Y k Z", "transformační"** → Hero's Journey
3. **"Film", "scénář", "narativní arch"** → Save the Cat
4. **"Pohádka", "dětský příběh", "jednoduchý"** → Pixar Story Spine
5. **Wallace evidence-review článek** (claim vs. evidence vs. reality) → South Park (causal + pivot dominantní)

V SKILL output zmiň ve 2 větách proč jsi zvolil ten framework.

## Pipeline

### Krok 1 — Parse input

Vstup může být:
- **Text** přímo v promptu (uživatel napsal příběh)
- **URL** (article) — stáhni přes `WebFetch` nebo `defuddle` skill
- **Cesta k souboru** (`.md`, `.txt`)

Vytvoř slug z titulku (kebab-case, ascii, max 50 chars). Slug = filename stem.

### Krok 2 — Rozseč na beats

Mentální proces (žádný subprocess LLM call — Claude to udělá sám):
1. Identifikuj 5-12 hlavních beatů (závisí na frameworku — South Park 5-9, Pixar 6, Save the Cat 15, Hero's Journey 8-12).
2. Pro každý beat napiš **3-12 slov** krátký label (musí se vejít na sticky note).
3. Mezi beats zvol connectory (slova z tabulky výše) — preferuj kontrast a kauzalitu, vyhni se monotónnímu "and/then".
4. Přiřaď color category (setup/conflict/insight/resolution/mentor).

### Krok 3 — Generuj Excalidraw JSON

**Layout (pro sticky notes, default):**
- Plátno: viewBackgroundColor `#ffffff`, gridSize 20.
- Karty horizontálně v jedné řadě (pokud beats ≤ 6), nebo 2 řady (pokud > 6).
- Card size: width 220, height 140. Mezi kartami gap 80 px (na šipku s labelem).
- Pisátkový font: `"fontFamily": 1` (Virgil) na všech textech.
- Stroke: `"roughness": 1` (mírně skicovité — Excalidraw default look).
- Pozice (x,y) absolutní px; první karta v `(100, 200)`.

**Excalidraw element types použité:**
- `rectangle` s `roundness: {type: 3}` = sticky note (rounded corners)
- `text` umístěn dovnitř karty (vystředěný) nebo nad/pod šipkou jako label
- `arrow` s `startBinding` / `endBinding` propojený s elementId karet
- (Volitelné) `ellipse` mini-ikonka v rohu karty

**JSON skeleton** — vyplň podle počtu beats:

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [
    {
      "id": "card-1",
      "type": "rectangle",
      "x": 100, "y": 200,
      "width": 220, "height": 140,
      "strokeColor": "#92400e",
      "backgroundColor": "#fef3c7",
      "fillStyle": "solid",
      "strokeWidth": 2,
      "roundness": {"type": 3},
      "roughness": 1
    },
    {
      "id": "label-1",
      "type": "text",
      "x": 120, "y": 240,
      "width": 180, "height": 60,
      "text": "Apigenin everywhere\\nin sleep stacks",
      "fontFamily": 1,
      "fontSize": 20,
      "textAlign": "center",
      "verticalAlign": "middle",
      "strokeColor": "#000000"
    },
    {
      "id": "arrow-1-2",
      "type": "arrow",
      "x": 320, "y": 270, "width": 80, "height": 0,
      "points": [[0,0],[80,0]],
      "startBinding": {"elementId": "card-1", "focus": 0.0, "gap": 5},
      "endBinding":   {"elementId": "card-2", "focus": 0.0, "gap": 5},
      "strokeColor": "#1e293b",
      "strokeWidth": 2,
      "endArrowhead": "arrow"
    },
    {
      "id": "connector-label-1-2",
      "type": "text",
      "x": 340, "y": 245,
      "width": 60, "height": 25,
      "text": "But",
      "fontFamily": 1,
      "fontSize": 16,
      "textAlign": "center",
      "strokeColor": "#991b1b"
    }
  ],
  "appState": {"viewBackgroundColor": "#ffffff", "gridSize": 20},
  "files": {}
}
```

**Důležité layout invarianty:**
- Každý `text` element musí mít unikátní `id`.
- `arrow.startBinding.elementId` a `endBinding.elementId` musí odkazovat na **existující** card id.
- Connector label umisti zhruba uprostřed šipky — `x = arrow.x + arrow.width/2 - label.width/2, y = arrow.y - 30`.
- Pokud máš 7+ karet, druhá řada `y = 450` (první řada `y = 200`).

### Krok 4 — Ulož `.excalidraw` soubor

```
~/Obsidian/feynman/Visualizations/YYYY-MM-DD-<slug>.excalidraw
```

Použij **Write tool** s celým JSON content jako string.

### Krok 5 — Renderuj PNG

Spusť renderer (Playwright + headless Chromium, ~3-5 s):

```bash
cd ~/.claude/skills/story-canvas/references
uv run python render_excalidraw.py ~/Obsidian/feynman/Visualizations/<slug>.excalidraw \
  --output ~/Obsidian/feynman/Visualizations/<slug>.png \
  --scale 2 --width 1920
```

**Setup (pokud renderer nikdy nejel):**
```bash
cd ~/.claude/skills/story-canvas/references
uv sync
uv run playwright install chromium
```

Renderer vytiskne cestu k PNG.

### Krok 6 — Self-review (povinný 1× iterace pro default)

1. **Přečti vygenerovaný PNG** tool `Read`em.
2. Zkontroluj checklist:
   - [ ] Všechny karty mají viditelný čitelný text (žádné cropping)?
   - [ ] Connector words (But/Therefore/…) jsou viditelné u šipek?
   - [ ] Šipky míří mezi správné karty (žádné křížení přes karty)?
   - [ ] Barvy karet odpovídají category (setup/conflict/insight/resolution)?
   - [ ] Layout je čitelný, žádné překryty?
3. Pokud je něco zlomené:
   - Uprav JSON (změň pozice, rozšiř karty, přepiš text na kratší).
   - Re-render.
   - Re-Read PNG.
4. Pokud je čistý → done.

### Krok 7 — Output uživateli

Vypiš:
```
✅ Story canvas vytvořen ({framework})

📂 Soubory:
   .excalidraw  ~/Obsidian/feynman/Visualizations/<slug>.excalidraw
   .png         ~/Obsidian/feynman/Visualizations/<slug>.png

📋 Beats:
   1. [setup]    Apigenin everywhere in sleep stacks  →  But
   2. [conflict] Trials tested chamomile, not apigenin →  Therefore
   3. [insight]  PK never measured in humans  →  Yet
   ...

🖼 Preview: <attach PNG using Read>
```

Pak Read PNG ještě jednou aby uživatel viděl finální výsledek inline.

## Iterace na zpětnou vazbu uživatele

Pokud po výstupu uživatel řekne:
- **"přepiš jako Hero's Journey"** → změň framework, regeneruj beats + JSON, re-render.
- **"karta 3 je špatně"** → uprav text/barvu/pozici té karty, re-render.
- **"přidej icon ke každé kartě"** → přidej `ellipse` / emoji text element do rohu každé karty.
- **"je to moc malé / velké"** → upravuj font sizes / card dimensions.

Vždy je možnost — neříkej "to nejde". Excalidraw JSON je plně přepsatelný; render je rychlý.

## Příklady invocation

```
> rozkresli mi tenhle článek jako příběh: https://www.drwilliamwallace.com/notes/apigenin-...

> udělej storyboard Hero's Journey pro: Po pádu z koně cyklista začne trénovat...

> South Park metodou rozbij ten kreatin článek
```

## Co skill NEDĚLÁ

- Nevolá Gemini / OpenAI / external LLM API. Beats generuje Claude Code přímo (ty).
- Nehledá obrázky / fotky on-line — diagram je čistě text + tvary.
- Nepublikuje nikam (no Telegram, no upload) — výstup je jen na disku / ve vaultu.
- Nepoužívá Excalidraw MCP / canvas server. Generuje statické `.excalidraw` JSON soubory.

## Reference / poznámky

- Excalidraw JSON spec: https://github.com/excalidraw/excalidraw/blob/master/dev-docs/docs/codebase/json-schema.mdx
- South Park storytelling secret: Stone & Parker přednáška NYU 2011
- Tutorial co inspiroval: youtu.be/nUIm3lqwnWU (Zsolt's Visual PKM)
- Renderer používá Playwright + load excalidraw.com offline → screenshot

## ⚠️ Povinná kontrola před odevzdáním

Každý vyrenderovaný vizuál projdi skillem **`vizualni-kontrola`**
(`~/.claude/skills/vizualni-kontrola/SKILL.md`): render → **podívej se na PNG** → hledej
text přes čáry/značky, kolize popisků, přetečení okrajů a popisky, které nesouhlasí
s přepočítanými čísly → oprav → re-render. Vygenerovat ≠ hotovo.
