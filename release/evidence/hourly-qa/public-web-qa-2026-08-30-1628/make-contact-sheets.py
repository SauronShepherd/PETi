from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

root = Path('release/evidence/hourly-qa/public-web-qa-2026-08-30-1628')
route_dir = root / 'route-audit'
fail_dir = root / 'failed-interactions'
routes = ['HOME','SCAN','HISTORY','PROFILE','AGENTS','CARE','BODY_CHECK','RECORDS','ASSISTANT','PLANS','SETTINGS','FEEDBACK','COLLABORATION','LIBRARY','ADMIN']
viewports = ['desktop','tablet','mobile']
font = ImageFont.load_default()

def label(draw, xy, text):
    draw.rectangle([xy[0], xy[1], xy[0] + len(text)*7 + 8, xy[1] + 16], fill=(255,255,255))
    draw.text((xy[0]+4, xy[1]+3), text, fill=(0,0,0), font=font)

def sheet(paths, out, cols=3, thumb_w=360):
    thumbs = []
    for p, title in paths:
        img = Image.open(p).convert('RGB')
        ratio = thumb_w / img.width
        thumb_h = max(1, int(img.height * ratio))
        img = img.resize((thumb_w, thumb_h))
        thumbs.append((img, title))
    rows = (len(thumbs) + cols - 1) // cols
    row_h = max(img.height for img, _ in thumbs) + 24
    canvas = Image.new('RGB', (cols * thumb_w, rows * row_h), (242,242,242))
    draw = ImageDraw.Draw(canvas)
    for i, (img, title) in enumerate(thumbs):
        x = (i % cols) * thumb_w
        y = (i // cols) * row_h
        canvas.paste(img, (x, y + 20))
        label(draw, (x + 4, y + 2), title)
    canvas.save(out)

for vp in viewports:
    paths = []
    for route in routes:
        slug = route.lower().replace('_','-')
        p = route_dir / f'{slug}-{vp}.png'
        if p.exists():
            paths.append((p, f'{route} {vp}'))
    sheet(paths, root / f'contact-sheet-routes-{vp}.jpg', cols=3, thumb_w=360)

fail_paths = []
for p in sorted(fail_dir.glob('extended-interactions-*/test-failed-1.png')):
    fail_paths.append((p, p.parent.name.replace('extended-interactions-', '')[:44]))
if fail_paths:
    sheet(fail_paths, root / 'contact-sheet-failures.jpg', cols=3, thumb_w=360)
print('created contact sheets')
