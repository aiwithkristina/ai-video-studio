"""The user's look: colors, fonts, social handle. Every effect draws with these, never with hardcoded values.

brand.json (all keys optional, missing ones fall back to the defaults below):
{
  "colors": {"primary": "#0725B0", "background": "#F2EFEA", "text": "#3E3A36", "light": "#FFFFFF"},
  "fonts":  {"display": "Archivo", "body": "Archivo", "hand": "Nothing You Could Do", "label": "Space Mono"},
  "handle": "@yourname"
}
A font can be a Google Fonts family from the list below (downloaded once, free OFL license)
or a path to any .ttf/.otf file on your computer.
"""
import json
import os
import urllib.parse
import urllib.request

from PIL import ImageFont

DEFAULT = {
    "colors": {
        "primary": "#0725B0",     # main accent: highlights, cards, charts
        "background": "#F2EFEA",  # paper / backdrop color
        "text": "#3E3A36",        # dark text on light backgrounds
        "light": "#FFFFFF",       # light text on video
        "secondary": "#E5DED4",   # soft second surface
        "line": "#CCC7BE",        # thin borders
    },
    "fonts": {"display": "Archivo", "body": "Archivo", "hand": "Nothing You Could Do", "label": "Space Mono"},
    "handle": "",
}

# Free (SIL Open Font License) families the engine can fetch from the official Google Fonts repository.
GOOGLE_FONTS = {
    "Archivo": "ofl/archivo/Archivo[wdth,wght].ttf",
    "Nothing You Could Do": "ofl/nothingyoucoulddo/NothingYouCouldDo.ttf",
    "Space Mono": "ofl/spacemono/SpaceMono-Bold.ttf",
    "Inter": "ofl/inter/Inter[opsz,wght].ttf",
    "Montserrat": "ofl/montserrat/Montserrat[wght].ttf",
    "Caveat": "ofl/caveat/Caveat[wght].ttf",
}
GOOGLE_RAW = "https://github.com/google/fonts/raw/main/"


def fonts_dir():
    d = os.environ.get("KFX_FONTS_DIR") or os.path.join(os.path.expanduser("~"), ".cache", "kfx", "fonts")
    os.makedirs(d, exist_ok=True)
    return d


def hex_rgb(value):
    v = value.lstrip("#")
    if len(v) == 3:
        v = "".join(c * 2 for c in v)
    return tuple(int(v[i:i + 2], 16) for i in (0, 2, 4))


def resolve_font(name):
    """A font file path for a family name or a path."""
    if os.path.isfile(os.path.expanduser(name)):
        return os.path.expanduser(name)
    if name not in GOOGLE_FONTS:
        raise SystemExit(f"Font '{name}' is not a file and not in the built-in list {sorted(GOOGLE_FONTS)}. "
                         "Put the path to a .ttf file in brand.json instead.")
    rel = GOOGLE_FONTS[name]
    local = os.path.join(fonts_dir(), os.path.basename(rel))
    if not os.path.exists(local):
        url = GOOGLE_RAW + urllib.parse.quote(rel)
        print(f"Downloading font {name} (free OFL license) ...")
        urllib.request.urlretrieve(url, local + ".part")
        os.replace(local + ".part", local)
    return local


class Brand:
    def __init__(self, data=None):
        data = data or {}
        self.colors = {**DEFAULT["colors"], **data.get("colors", {})}
        self.fonts = {**DEFAULT["fonts"], **data.get("fonts", {})}
        self.handle = data.get("handle", DEFAULT["handle"])
        self._font_cache = {}

    @classmethod
    def load(cls, path=None):
        if not path:
            return cls()
        with open(path, encoding="utf-8") as f:
            return cls(json.load(f))

    def rgb(self, name):
        """Color as an (r, g, b) tuple: brand.rgb('primary')."""
        return hex_rgb(self.colors[name])

    def tint(self, name, amount):
        """A color mixed toward white (amount > 0) or black (amount < 0): brand.tint('primary', 0.5)."""
        c = self.rgb(name)
        target = 255 if amount > 0 else 0
        return tuple(int(v + (target - v) * abs(amount)) for v in c)

    def font(self, role="display", size=80, weight=800, width=100):
        """PIL font for a role ('display', 'body', 'hand', 'label'). Variable fonts get the weight and width axes set."""
        key = (role, size, weight, width)
        if key in self._font_cache:
            return self._font_cache[key]
        f = ImageFont.truetype(resolve_font(self.fonts[role]), size)
        try:
            axes = f.get_variation_axes()
            values = []
            for ax in axes:
                tag = ax.get("name", b"")
                tag = (tag.decode("utf-8", "ignore") if isinstance(tag, bytes) else str(tag)).lower()
                lo, hi = ax["minimum"], ax["maximum"]
                want = weight if "weight" in tag or "wght" in tag else width if "width" in tag or "wdth" in tag else ax["default"]
                values.append(max(lo, min(hi, want)))
            f.set_variation_by_axes(values)
        except (OSError, AttributeError):
            pass  # static font: no axes to set
        self._font_cache[key] = f
        return f
