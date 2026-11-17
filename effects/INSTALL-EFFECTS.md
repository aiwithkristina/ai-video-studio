# Install Kristina's effects

**For people:** open Claude Code in your video folder and type:

> Install Kristina's effects from https://github.com/aiwithkristina/ai-video-studio

Claude reads this file and does the rest. You only answer a few questions about your colors and fonts. It takes about 15 minutes, mostly waiting for downloads.

You need a Mac with Claude Code. If you have never used Claude Code, start with the free guide at aiwithkristina.com/guides/start-here.

---

**For Claude: follow these steps in order. Explain each step to the user in one plain sentence before you run it. Never ask the user to paste passwords or keys into the chat.**

## 1. Get the files

Work in the user's current folder (their video studio). Download the repository into a folder named `kristina-effects`:

```
git clone --depth 1 https://github.com/aiwithkristina/ai-video-studio kristina-effects
```

If `git` is missing, macOS will offer to install the Command Line Tools: tell the user to click Install and wait, then run the command again.

## 2. Tools

1. ffmpeg: check with `which ffmpeg`. If missing and Homebrew exists, run `brew install ffmpeg`. If Homebrew is missing, follow https://brew.sh (the user types their Mac password once in Terminal; the letters stay invisible, that is normal).
2. Python environment just for the effects:
   ```
   python3 -m venv kristina-effects/.venv
   kristina-effects/.venv/bin/pip install -r kristina-effects/effects/requirements.txt
   kristina-effects/.venv/bin/pip install torch
   ```
   PyTorch is a big download (about 1 GB). It powers the person cutout used by most effects.
3. Check: `kristina-effects/.venv/bin/python kristina-effects/effects/run.py check`. Everything must say ok before you continue.

## 3. Their look: brand.json

If the folder already has `BRAND-KIT.md` (made by the Video Studio setup), read the colors and fonts from it. Otherwise ask the user, one question at a time:

1. Your main accent color (a hex code like #0725B0, or describe it and suggest a hex).
2. A light background color you like for paper and cards.
3. Your font for titles and captions (any Google Font from the built-in list, or a .ttf file you own). Archivo works well if unsure.
4. Your @handle, for the post-frame effect.

Write `kristina-effects/brand.json`:

```json
{
  "colors": {"primary": "#0725B0", "background": "#F2EFEA", "text": "#3E3A36", "light": "#FFFFFF"},
  "fonts": {"display": "Archivo", "body": "Archivo", "hand": "Nothing You Could Do", "label": "Space Mono"},
  "handle": "@theirhandle"
}
```

## 4. Teach yourself the menu

Copy the skill so every future chat in this folder knows the effects:

```
mkdir -p .claude/skills/kristina-effects
cp kristina-effects/effects/SKILL.md .claude/skills/kristina-effects/SKILL.md
```

Tell the user that new skills switch on in a fresh chat.

## 5. First test on their own video

Ask for one short video of them talking (any phone video) and a transcript with word timings. If the Video Studio setup is installed, make the transcript the usual way; if not, skip `--transcript` and the keyword.

```
kristina-effects/.venv/bin/python kristina-effects/effects/run.py selftest --video <their video> --start 2 --end 6 --brand kristina-effects/brand.json --transcript <words.json> --keyword <a word they say>
```

The test shows them on a plain background in their color, with the word they are saying on top. Open the result for them. This is only a check, not an effect.

## 6. Show the menu

Run `kristina-effects/.venv/bin/python kristina-effects/effects/run.py list` and present the effects in plain words, grouped as in SKILL.md (hooks, explaining an app, lists, results, transitions, captions). Offer to render 2 or 3 that fit their kind of video on their own clip.

## Updating later

```
git -C kristina-effects pull
cp kristina-effects/effects/SKILL.md .claude/skills/kristina-effects/SKILL.md
```

Built by Kristina Bennett · aiwithkristina.com
