# kfx engine

The shared base behind every effect in this pack. An effect only describes the look. The engine does the rest on **your** video:

| Part | What it does | File |
|---|---|---|
| Clip | Cuts the seconds you pick from your video, crops to 9:16, keeps the sound | `kfx/clip.py`, `kfx/video.py` |
| Cutout | Separates you from the background on every frame, so graphics can sit behind you | `kfx/matte.py` |
| Words | Reads your transcript so an effect can fire on the exact word you say | `kfx/words.py` |
| Brand | Your colors, fonts and @handle from `brand.json` | `kfx/brand.py` |
| Drawing | Text, cards from screenshots, 3D tilt, pop-in timing | `kfx/draw.py` |

Frames and cutouts are cached in `~/.cache/kfx/`, so the second render of the same clip is quick.

## Requirements

- ffmpeg (`brew install ffmpeg` on a Mac)
- Python 3.9+ with `pip install -r effects/requirements.txt`
- PyTorch only for effects that put things behind you (`pip install torch`)

Check everything with:

```
python effects/run.py check
```

## Try it on your own clip

```
python effects/run.py selftest --video my-video.mp4 --start 3 --end 7 --transcript words.json --keyword ai
```

You should see yourself on a plain background in your brand color, the word you are saying at the top, and your keyword popping in when you say it. If that works, every effect will work.

## Your look: brand.json

```json
{
  "colors": {"primary": "#0725B0", "background": "#F2EFEA", "text": "#3E3A36", "light": "#FFFFFF"},
  "fonts": {"display": "Archivo", "body": "Archivo", "hand": "Nothing You Could Do"},
  "handle": "@yourname"
}
```

Fonts can be a family from the built-in list (Archivo, Inter, Montserrat, Caveat, Nothing You Could Do; downloaded free from Google Fonts) or a path to any `.ttf` file you own.

## Transcripts

Word timings in ElevenLabs or Whisper JSON. The Video Studio setup makes them for you. Effects that react to words need `--transcript`.

## Credits and licenses

- Person cutout: [Robust Video Matting](https://github.com/PeterL1n/RobustVideoMatting) (GPL-3.0), downloaded by PyTorch on first use, not included here.
- Fonts: SIL Open Font License, fetched from [google/fonts](https://github.com/google/fonts).

Built by Kristina Bennett · aiwithkristina.com
