from pathlib import Path
import json, html, shutil

ROOT = Path(__file__).resolve().parent
SITE_URL = "https://beneaththeashesdayz.github.io"

traders = json.loads((ROOT / "traders.json").read_text(encoding="utf-8"))
index_template = (ROOT / "_index.template.html").read_text(encoding="utf-8")
profile_template = (ROOT / "_profile.template.html").read_text(encoding="utf-8")

def esc(value):
    return html.escape(str(value), quote=True)

def li(items):
    return "".join(f"<li>{esc(item)}</li>" for item in items)

(ROOT / "traders").mkdir(exist_ok=True)
(ROOT / "traders" / "index.html").write_text(
    index_template.replace("__TRADERS__", json.dumps(traders)),
    encoding="utf-8"
)

for t in traders:
    out = ROOT / "traders" / t["slug"]
    out.mkdir(parents=True, exist_ok=True)
    canonical = f"{SITE_URL}/traders/{t['slug']}/"
    og_image = f"{SITE_URL}/{t['image']}"
    chips = "".join(f'<span class="chip">{esc(x.strip())}</span>' for x in t["specialty"].split("•"))
    page = profile_template
    replacements = {
        "__NAME__": esc(t["name"]),
        "__TITLE__": esc(t["title"]),
        "__LOCATION__": esc(t["location"]),
        "__REGION__": esc(t["region"]),
        "__CURRENCY__": esc(t["currency"]),
        "__SPECIALTY__": esc(t["specialty"]),
        "__SUMMARY__": esc(t["summary"]),
        "__IMAGE__": esc(t["image"]),
        "__OG_IMAGE__": esc(og_image),
        "__CANONICAL__": esc(canonical),
        "__CHIPS__": chips,
        "__BUYS__": li(t["buys"]),
        "__SELLS__": li(t["sells"]),
        "__NOTES__": li(t["notes"]),
    }
    for key, value in replacements.items():
        page = page.replace(key, value)
    (out / "index.html").write_text(page, encoding="utf-8")

print(f"Built {len(traders)} trader profiles.")
