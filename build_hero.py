"""Compose the profile hero: ASCII portrait (left) + role/terminal box (right).

One SVG, inline attributes + <defs> gradients only (no <style>/class), so GitHub's
SVG sanitiser keeps every colour. The portrait comes from a local rembg alpha matte
of the GitHub avatar; the right box is a dark terminal card with typed-in roles,
info rows, skill pills and social icons.
"""
import os
import urllib.request

import numpy as np
from PIL import Image

AVATAR_URL = "https://github.com/RFNOACH.png?size=460"
AVATAR_PATH = "assets/avatar.png"
CUTOUT_PATH = "assets/cutout.png"
OUT = "hero.svg"

COLS = 64
RAMP = " .:-=+*#%@"
ALPHA_CUT, FLOOR, GAMMA, BODY_KEEP = 0.35, 0.05, 1.0, 0.82

FONT = "ui-monospace,SFMono-Regular,Menlo,Consolas,monospace"
DOTS = (("#ff5f56", 20), ("#ffbd2e", 36), ("#27c93f", 52))


def fetch_avatar():
    if not os.path.exists(AVATAR_PATH):
        os.makedirs("assets", exist_ok=True)
        urllib.request.urlretrieve(AVATAR_URL, AVATAR_PATH)


def cutout():
    if not os.path.exists(CUTOUT_PATH):
        from rembg import remove
        remove(Image.open(AVATAR_PATH)).save(CUTOUT_PATH)
    img = Image.open(CUTOUT_PATH)
    l, t, r, b = img.split()[3].point(lambda v: 255 if v > 60 else 0).getbbox()
    b = t + int((b - t) * BODY_KEEP)          # keep head + shoulders
    return img.crop((l, t, r, b))


def to_ascii(img, cols):
    a = np.asarray(img)
    alpha = a[:, :, 3].astype(float) / 255
    lum = np.asarray(Image.fromarray(a[:, :, :3]).convert("L"), dtype=float)
    subject = alpha > 0.5
    lo, hi = np.percentile(lum[subject], 1), np.percentile(lum[subject], 99)
    norm = np.clip((lum - lo) / (hi - lo), 0, 1)
    rows = round(img.height / img.width * cols * 0.5)

    def down(x):
        s = Image.fromarray((x * 255).astype(np.uint8)).resize((cols, rows), Image.LANCZOS)
        return np.asarray(s, dtype=float) / 255

    n, m = down(norm), down(alpha)
    out = []
    for y in range(rows):
        line = []
        for x in range(cols):
            v = n[y, x] ** GAMMA
            if m[y, x] < ALPHA_CUT or v < FLOOR:
                line.append(" ")
            else:
                t = (v - FLOOR) / (1 - FLOOR)
                line.append(RAMP[min(len(RAMP) - 1, int(t * len(RAMP)))])
        out.append("".join(line))
    return out


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


# ---- layout ---------------------------------------------------------------

W, H = 1180, 572
LP = (16, 16, 440, 540)          # left window x, y, w, h
RP = (472, 16, 692, 540)
CHROME = 30
PX = RP[0] + 28                  # right content left edge
RX = RP[0] + RP[2] - 28          # right content right edge
PORTRAIT_CAP = 360

ROLES = ["AI / ML Engineer", "LLM Systems Engineer", "RAG Architect",
         "Agent Builder", "MLOps Engineer"]
ROLE_W = [192, 240, 156, 156, 168]   # px width per role at font-size 20

INFO = [
    ("Location", "Tel Aviv, Israel"),
    ("Education", "Computer Science · Machine Learning"),
    ("Focus", "LLM evaluation · RAG · autonomous agents"),
    ("Portfolio", "github.com/RFNOACH"),
    ("Email", "noach@bizzup.app"),
]
PILLS = ["Python", "PyTorch", "LangChain", "LlamaIndex", "FastAPI", "Docker",
         "Kubernetes", "Qdrant", "Postgres", "AWS", "MLflow", "W&B", "LangGraph"]

GH_ICON = "M16 8a8 8 0 0 0-2.5 15.6c.4.07.55-.17.55-.38v-1.3c-2.2.48-2.67-1.06-2.67-1.06-.36-.92-.88-1.16-.88-1.16-.72-.5.05-.48.05-.48.8.056 1.22.82 1.22.82.71 1.22 1.86.87 2.32.66.07-.51.28-.87.5-1.06-1.75-.2-3.6-.88-3.6-3.9 0-.86.3-1.57.82-2.12-.08-.2-.36-1 .08-2.1 0 0 .67-.21 2.2.8a7.6 7.6 0 0 1 4 0c1.53-1.03 2.2-.81 2.2-.81.44 1.1.16 1.9.08 2.1.5.55.8 1.26.8 2.12 0 3.03-1.85 3.7-3.61 3.9.28.24.54.72.54 1.46v2.16c0 .21.14.46.55.38A8 8 0 0 0 16 8Z"
LI_ICON = "M11 13h2.4v1.1h.03c.34-.62 1.16-1.28 2.39-1.28 2.56 0 3.03 1.63 3.03 3.75V22h-2.5v-3.6c0-.86-.02-1.97-1.23-1.97-1.23 0-1.42.94-1.42 1.9V22H11V13Zm-3.2 0h2.5v9H7.8v-9Zm1.25-3.6a1.45 1.45 0 1 1 0 2.9 1.45 1.45 0 0 1 0-2.9Z"
GLOBE_ICON = "M16 8a8 8 0 1 0 0 16 8 8 0 0 0 0-16Zm5.9 7.3h-2.9a13 13 0 0 0-.9-4.2 6.06 6.06 0 0 1 3.8 4.2ZM16 9.9c.6.8 1.2 2.3 1.4 5.4h-2.8c.2-3.1.8-4.6 1.4-5.4Zm-2.1.2a13 13 0 0 0-.9 5.2h-2.9a6.06 6.06 0 0 1 3.8-5.2ZM10.1 16.7H13c.1 2 .5 3.6.9 4.4a6.06 6.06 0 0 1-3.8-4.4Zm5.9 4.4c-.6-.8-1.2-2.3-1.4-4.4h2.8c-.2 2.1-.8 3.6-1.4 4.4Zm2.1-.2c.4-.8.8-2.4.9-4.2h2.9a6.06 6.06 0 0 1-3.8 4.2Z"

SOCIALS = [
    ("https://github.com/RFNOACH", f'<path d="{GH_ICON}" fill="#c9d1d9"/>'),
    ("https://www.linkedin.com/in/althay-noach-ramallo/", f'<path d="{LI_ICON}" fill="#c9d1d9"/>'),
    ("mailto:noach@bizzup.app",
     '<rect x="8" y="11.5" width="16" height="10" rx="1.5" fill="#c9d1d9"/>'
     '<path d="M8.6 12.4 16 17.2 23.4 12.4" fill="none" stroke="#0d1117" stroke-width="1.5"/>'),
    ("https://github.com/RFNOACH", f'<path d="{GLOBE_ICON}" fill="#c9d1d9"/>'),
]


def window(x, y, w, h, title):
    p = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="#0d1117" stroke="#30363d"/>']
    p.append(f'<line x1="{x}" y1="{y + CHROME}" x2="{x + w}" y2="{y + CHROME}" stroke="#30363d"/>')
    for col, dx in DOTS:
        p.append(f'<circle cx="{x + dx}" cy="{y + 15}" r="5" fill="{col}"/>')
    p.append(f'<text x="{x + w / 2}" y="{y + 19}" fill="#7d8590" font-size="12.5" '
             f'text-anchor="middle">{title}</text>')
    return "".join(p)


def portrait_group(rows):
    lx, ly, lw, lh = LP
    avail_w, avail_h = lw - 32, lh - CHROME - 30
    n = len(rows)
    char_w = avail_w / COLS
    pitch = char_w * 2
    cap = min(avail_h, PORTRAIT_CAP)
    if n * pitch > cap:
        f = cap / (n * pitch)
        char_w *= f
        pitch *= f
    aw = COLS * char_w
    x0 = lx + (lw - aw) / 2
    y0 = ly + CHROME + (lh - CHROME - n * pitch) / 2 + pitch
    # Looping "unfold -> hold -> fold" reveal: each row's clip width rides one shared
    # T-second cycle, its phase baked into keyTimes so a wipe travels top->bottom on the
    # way in and out. repeatCount indefinite keeps it going forever.
    td, st, hold, gap = 0.10, 0.05, 2.4, 0.7        # type, stagger, hold-open, blank gap
    reveal_span = n * st + td
    fold_start = reveal_span + hold
    T = fold_start + (n * st + td) + gap

    p = ["<g>"]
    for i, row in enumerate(rows):
        y = y0 + i * pitch
        a, ae = i * st, i * st + td                 # unfold window
        b, be = fold_start + i * st, fold_start + i * st + td  # fold window
        times, vals = [0.0], [0]
        if a > 0:
            times.append(a); vals.append(0)
        times += [ae, b, be, T]
        vals += [aw, aw, 0, 0]
        kt = ";".join(f"{t / T:.4f}" for t in times)
        vv = ";".join(f"{v:.1f}" if isinstance(v, float) else str(v) for v in vals)
        cid = f"pr{i}"
        p.append(f'<clipPath id="{cid}"><rect x="{x0:.1f}" y="{y - pitch:.1f}" '
                 f'height="{pitch:.1f}" width="0"><animate attributeName="width" '
                 f'values="{vv}" keyTimes="{kt}" dur="{T:.2f}s" '
                 f'repeatCount="indefinite"/></rect></clipPath>')
        p.append(f'<g clip-path="url(#{cid})"><text x="{x0:.1f}" y="{y:.1f}" '
                 f'fill="url(#ink)" font-size="{pitch:.1f}" textLength="{aw:.1f}" '
                 f'lengthAdjust="spacing" xml:space="preserve">{esc(row)}</text></g>')
    cy = y0 + (n - 1) * pitch
    p.append(f'<rect x="{x0 + aw + 3:.1f}" y="{cy - pitch * 0.8:.1f}" width="{char_w:.1f}" '
             f'height="{pitch * 0.8:.1f}" fill="#c9d1d9" opacity="0"><animate '
             f'attributeName="opacity" values="0;1;1;0;0;1" keyTimes="0;.01;.5;.51;.99;1" '
             f'dur="1.06s" repeatCount="indefinite"/></rect>')
    p.append("</g>")
    return "".join(p)


def roles_group():
    ry, rh, T, yb = 148, 30, 15, 170
    p = ["<defs>"]
    for i, w in enumerate(ROLE_W):
        s = i * 0.2
        if i == 0:
            kt, vals = "0;.113;.199;.2;1", f"0;{w};{w};0;0"
        else:
            kt = f"0;{s:.3f};{s + .113:.3f};{s + .199:.3f};{s + .2:.3f};1"
            vals = f"0;0;{w};{w};0;0"
        p.append(f'<clipPath id="ty{i}"><rect x="{PX}" y="{ry}" height="{rh}" width="0">'
                 f'<animate attributeName="width" values="{vals}" keyTimes="{kt}" '
                 f'dur="{T}s" repeatCount="indefinite"/></rect></clipPath>')
    p.append("</defs>")
    for i, role in enumerate(ROLES):
        s = i * 0.2
        if i == 0:
            okt, ov = "0;.199;.2;1", "1;1;0;0"
        else:
            okt = f"0;{s:.3f};{s + .001:.3f};{s + .199:.3f};{s + .2:.3f};1"
            ov = "0;0;1;1;0;0"
        p.append(f'<g clip-path="url(#ty{i})"><g opacity="0"><animate attributeName="opacity" '
                 f'values="{ov}" keyTimes="{okt}" dur="{T}s" repeatCount="indefinite"/>'
                 f'<text x="{PX}" y="{yb}" fill="#39d353" font-size="20" '
                 f'font-weight="600">{esc(role)}</text></g></g>')
    seq = []
    for i, w in enumerate(ROLE_W):
        base = i * 0.2
        for frac, val in [(0, PX), (.113, PX + w), (.199, PX + w), (.2, PX)]:
            seq.append((base + frac, val))
    seq[-1] = (1.0, PX)
    valstr = ";".join(str(v) for _, v in seq)
    ktstr = ";".join(f"{t:.3f}" for t, _ in seq)
    p.append(f'<rect y="150" width="11" height="24" fill="#39d353">'
             f'<animate attributeName="x" values="{valstr}" keyTimes="{ktstr}" dur="{T}s" '
             f'repeatCount="indefinite"/><animate attributeName="opacity" values="1;0;1" '
             f'dur=".9s" repeatCount="indefinite"/></rect>')
    return "".join(p)


def info_group():
    p, y = [], 232
    for i, (label, value) in enumerate(INFO):
        beg = 0.6 + i * 0.18
        p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                 f'begin="{beg:.2f}s" dur=".4s" fill="freeze"/>'
                 f'<circle cx="{PX + 4}" cy="{y - 5}" r="3.5" fill="#39d353"/>'
                 f'<text x="{PX + 20}" y="{y}" fill="#7d8590" font-size="15">{label}</text>'
                 f'<text x="{PX + 150}" y="{y}" fill="#c9d1d9" font-size="15">{esc(value)}</text></g>')
        y += 36
    return "".join(p)


def pills_group():
    charw, padx, gap, maxw = 7.8, 24, 9, RX - PX
    lines, cur, x = [], [], 0
    for it in PILLS:
        w = len(it) * charw + padx
        if cur and x + gap + w > maxw:
            lines.append(cur); cur, x = [], 0
        if cur:
            x += gap
        cur.append((it, w)); x += w
    if cur:
        lines.append(cur)
    p = [f'<text x="{PX}" y="414" fill="#7d8590" font-size="13">// stack</text>']
    idx = 0
    for r, line in enumerate(lines[:2]):
        y = 428 + r * 40
        cx = PX
        for it, w in line:
            beg = 1.4 + idx * 0.08
            p.append(f'<g opacity="0"><animate attributeName="opacity" values="0;1" '
                     f'begin="{beg:.2f}s" dur=".35s" fill="freeze"/>'
                     f'<rect x="{cx:.1f}" y="{y}" width="{w:.1f}" height="30" rx="15" '
                     f'fill="#161b22" stroke="#30363d"/>'
                     f'<circle cx="{cx + 15:.1f}" cy="{y + 15}" r="3" fill="#39d353"/>'
                     f'<text x="{cx + 26:.1f}" y="{y + 20}" fill="#c9d1d9" '
                     f'font-size="14">{esc(it)}</text></g>')
            cx += w + gap
            idx += 1
    return "".join(p)


def socials_group():
    p = ['<g opacity="0"><animate attributeName="opacity" values="0;1" begin="2.4s" '
         'dur=".5s" fill="freeze"/>']
    for i, (href, inner) in enumerate(SOCIALS):
        p.append(f'<a xlink:href="{href}" target="_blank" rel="noopener">'
                 f'<g transform="translate({PX + i * 48},512)">'
                 f'<circle cx="16" cy="16" r="16" fill="#161b22" stroke="#30363d"/>'
                 f'{inner}</g></a>')
    p.append("</g>")
    return "".join(p)


def build(rows):
    p = [f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
         f'width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="{FONT}" role="img" '
         f'aria-label="Noach Ramallo - AI/ML Engineer">']
    p.append('<defs><linearGradient id="ink" x1="0" y1="0" x2="0" y2="1">'
             '<stop offset="0" stop-color="#ffffff"/><stop offset=".55" stop-color="#c9d1d9"/>'
             '<stop offset="1" stop-color="#8b949e"/></linearGradient></defs>')
    p.append(f'<rect width="{W}" height="{H}" fill="#010409"/>')
    p.append(window(*LP, "portrait.ascii"))
    p.append(portrait_group(rows))
    p.append(window(*RP, "noach@github: ~/whoami"))
    p.append(f'<text x="{PX}" y="82" fill="#7d8590" font-size="16">Hi, I\'m</text>')
    p.append(f'<text x="{PX}" y="126" fill="#f0f6fc" font-size="34" font-weight="700">Noach Ramallo</text>')
    p.append(roles_group())
    p.append(f'<line x1="{PX}" y1="196" x2="{RX}" y2="196" stroke="#21262d"/>')
    p.append(info_group())
    p.append(pills_group())
    p.append(socials_group())
    p.append("</svg>")
    return "".join(p)


if __name__ == "__main__":
    fetch_avatar()
    rows = to_ascii(cutout(), COLS)
    open(OUT, "w", encoding="utf-8").write(build(rows))
    print(f"{OUT}: {len(rows)} ascii rows")
