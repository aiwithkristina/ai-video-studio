---
name: kristina-effects
description: Menu of Kristina Bennett's video effects and caption animations for vertical talking videos (orbit cards, phone mockup, punch-in zoom, text behind head, word-by-word captions and more). Use when editing a video and the user wants an effect, a caption style, or asks what effects are available.
---

# Kristina's effects: menu and how to run them

All effects live in the folder this file was installed from (default `kristina-effects/`). Run them with that folder's Python:

```
kristina-effects/.venv/bin/python kristina-effects/effects/run.py <effect> --video <file> --start <s> --end <s> [--transcript words.json] [--brand brand.json] [options]
```

- Output is a vertical 1080x1920 mp4 with the original sound, saved to `renders/` unless `--out` is given.
- `--start/--end` pick the seconds of the video. Keep effect clips short: 2 to 5 seconds.
- `--brand` points to the user's `brand.json` (colors, fonts, @handle). Always pass it.
- `--transcript` is the word-timing JSON (ElevenLabs or Whisper). Effects marked **words** need it.
- `--focus x,y` tells zoom effects where the face is, as fractions of the frame (default 0.52,0.33).
- Every effect has `--help` with its own options.
- The first run on a new clip cuts the person out of the background (a minute or two). Later runs reuse it.

## Rules for using them well

1. Ask before adding an effect. Show what it will look like on their clip (render a short sample), then let them say yes or no.
2. One or two big effects per video. Never the same effect twice in a row.
3. Any app on screen must be a REAL screenshot of the real app (pass it with `--screen` or `--images`). Never draw or fake an interface.
4. If the user gave no images, effects show brand-colored placeholders. Never ship a video with placeholders: ask for real screenshots first.
5. Respect their editing rules (EDITING-RULES.md) over anything here.

## Effects (13)

| Run | Name | What it does | Needs | Key options |
|---|---|---|---|---|
| `01` | Orbit | Screenshot cards circle the person, passing behind and in front | cutout | `--images` 2-8 files |
| `02` | Screen wall | The wall behind fills with screenshots, tile by tile | cutout | `--images`, `--bottom` |
| `03` | App world | Split screen: real app on top, person below, cards fly into the app | | `--screen`, `--crop`, `--images` |
| `04` | Frame break | Video shrinks into a social post frame, person steps out of it | cutout | `--handle` |
| `05` | Punch-in zoom | Hard zoom on the face when a key word is said | words | `--keyword` (required), `--zoom` |
| `06` | Phone | 3D phone with a real app floats beside the person, turned toward them | cutout | `--screen`, `--crop`, `--side` |
| `07` | Checklist | Glass checklist at the top, items type in and get checked | | `--items`, `--title`, `--times` |
| `08` | Headline wall | Headline cards pile up behind, slow push-in | cutout | `--headlines` ("line one\|line two") |
| `09` | Zoom-through cut | Transition: zoom into one clip, out of the next | | `--next` (required), `--next-start`, `--next-end` |
| `10` | Growth chart | A glowing line chart draws itself behind the person | cutout | `--labels`, `--values`, `--scale`, `--tag` |
| `11` | Pull-back reveal | Video shrinks into a card inside a real app screen | | `--screen`, `--crop`, `--y` |
| `12` | Green screen | The room swaps to any image, no green screen needed | cutout | `--background`, `--keep-bottom` |
| `13` | Paper cut | Person becomes a paper cut-out on a collage, cut-out letters pop in | cutout | `--text` (1-5 letters) |

## Caption animations (3)

| Run | Name | What it does | Needs | Key options |
|---|---|---|---|---|
| `c1` | Word-by-word captions | One word at a time, key words bigger, entrance changes per sentence (pop, rise, drop) | words | `--keywords`, `--proper`, `--y`, `--scale` |
| `c2` | Text behind head | Huge words pop up behind the person the moment they say them | cutout, words | `--words` (required), `--show` |
| `c3` | Silhouette words | The spoken words write themselves along the person's outline, over the head | cutout, words | `--offset`, `--cut`, `--text` |

Best fits:
- Hook (first 3 seconds): `c2` text behind head, `05` punch-in zoom, `04` frame break.
- Explaining an app: `06` phone, `03` app world, `11` pull-back reveal, `12` green screen.
- Lists and steps: `07` checklist.
- "Everyone is talking about it": `08` headline wall, `02` screen wall, `01` orbit.
- Results and numbers: `10` growth chart.
- Scene change: `09` zoom-through cut.
- Playful moment: `13` paper cut, `c3` silhouette words.
- Whole video captions: `c1`.

## Putting an effect into the full edit

An effect renders a finished short clip. To use it inside a longer edit, render the effect for the exact seconds it covers, then cut it into the timeline in place of those seconds (same start and end, same sound). The sound is kept from the original, so lip sync stays exact.

Built by Kristina Bennett · aiwithkristina.com
