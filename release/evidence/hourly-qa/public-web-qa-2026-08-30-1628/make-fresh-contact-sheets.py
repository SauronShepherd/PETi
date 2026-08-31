from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
root = Path('release/evidence/hourly-qa/public-web-qa-2026-08-30-1628')
route_dir = root / 'fresh-route-audit'
routes = ['HOME','SCAN','HISTORY','PROFILE','AGENTS','CARE','BODY_CHECK','RECORDS','ASSISTANT','PLANS','SETTINGS','FEEDBACK','COLLABORATION','LIBRARY','ADMIN']
viewports = ['desktop','tablet','mobile']
font = ImageFont.load_default()
def sheet(paths, out, cols=3, thumb_w=360):
    thumbs=[]
    for p,title in paths:
        img=Image.open(p).convert('RGB')
        ratio=thumb_w/img.width
        img=img.resize((thumb_w,max(1,int(img.height*ratio))))
        thumbs.append((img,title))
    rows=(len(thumbs)+cols-1)//cols
    row_h=max(img.height for img,_ in thumbs)+24
    canvas=Image.new('RGB',(cols*thumb_w,rows*row_h),(242,242,242))
    draw=ImageDraw.Draw(canvas)
    for i,(img,title) in enumerate(thumbs):
        x=(i%cols)*thumb_w; y=(i//cols)*row_h
        canvas.paste(img,(x,y+20))
        draw.rectangle([x,y,x+len(title)*7+8,y+17], fill=(255,255,255))
        draw.text((x+4,y+3),title,fill=(0,0,0),font=font)
    canvas.save(out)
for vp in viewports:
    paths=[]
    for route in routes:
        p=route_dir / f'{route.lower().replace("_","-")}-{vp}.png'
        if p.exists(): paths.append((p,f'{route} {vp}'))
    sheet(paths, root / f'contact-sheet-fresh-routes-{vp}.jpg', cols=3, thumb_w=360)
print('created fresh contact sheets')
