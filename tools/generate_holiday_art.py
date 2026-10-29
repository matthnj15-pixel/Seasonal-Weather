#!/usr/bin/env python3
"""Create ten weather-aware holiday editions, each in square and 2:1 layouts.

Images are composited from the existing seasonal weather scenes. Decorations
are drawn at the edges to preserve a readable central forecast, and vary by
holiday, time of day, and weather. No external artwork or API is required.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
import hashlib
import math
import random

EVENTS = {
    "july4": ("summer", (217, 60, 70), (65, 145, 240)),
    "christmas": ("winter", (235, 66, 68), (42, 174, 115)),
    "newyear": ("winter", (235, 199, 108), (157, 185, 234)),
    "easter": ("spring", (237, 153, 191), (154, 212, 186)),
    "thanksgiving": ("fall", (231, 141, 64), (166, 83, 54)),
    "halloween": ("fall", (248, 135, 53), (136, 86, 192)),
    "memorial": ("spring", (188, 54, 72), (57, 110, 181)),
    "labor": ("summer", (247, 182, 95), (84, 155, 193)),
    "birthday_a": ("fall", (225, 179, 107), (194, 136, 173)),
    "birthday_b": ("summer", (242, 123, 157), (88, 212, 213)),
}
STATES = ("sunny", "partly", "cloudy", "rain", "heavy", "storm", "snow", "fog")
PHASES = ("day", "twilight", "night")
SIZES = {"square": (720, 720), "wide": (960, 480)}


def rgba(rgb, a=255):
    return tuple(rgb[:3]) + (int(a),)


def star_points(cx, cy, radius, count=5, inner=.46, rotation=-math.pi / 2):
    points = []
    for i in range(count * 2):
        angle = rotation + math.pi * i / count
        r = radius if i % 2 == 0 else radius * inner
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return points


def bell(draw, x, y, r, color):
    draw.arc((x-r, y-r, x+r, y+r), 190, 350, fill=rgba(color, 210), width=max(2, int(r/7)))
    draw.ellipse((x-r*.7, y+r*.36, x+r*.7, y+r*.56), fill=rgba(color, 230))
    draw.ellipse((x-r*.16, y+r*.53, x+r*.16, y+r*.80), fill=(248, 220, 137, 240))


def flower(draw, x, y, r, petal, center=(250,205,93)):
    for t in range(6):
        a = t * math.pi / 3
        dx, dy = r * .55 * math.cos(a), r * .55 * math.sin(a)
        draw.ellipse((x+dx-r*.45,y+dy-r*.45,x+dx+r*.45,y+dy+r*.45), fill=rgba(petal, 205))
    draw.ellipse((x-r*.27,y-r*.27,x+r*.27,y+r*.27),fill=rgba(center,255))


def balloon(draw, x, y, r, color, rng):
    draw.line((x,y+r*.85,x+rng.randint(-22,22),y+r*4), fill=(241,235,225,115), width=2)
    draw.ellipse((x-r*.76,y-r*1.15,x+r*.76,y+r*.86),fill=rgba(color,207),
                 outline=(250,244,227,130),width=2)
    draw.ellipse((x-r*.50,y-r*.88,x-r*.31,y-r*.20),fill=(255,255,255,88))
    draw.polygon([(x-6,y+r*.77),(x+6,y+r*.77),(x,y+r*1.04)],fill=rgba(color,238))


def pumpkin(draw, x, y, r, color=(234,119,51), glow=False):
    for offset in (-.51, -.22, .22, .51, 0):
        rr = r * (.64 if abs(offset) > .4 else .82)
        draw.ellipse((x+r*offset-rr,y-r*.82,x+r*offset+rr,y+r*.67),
                     fill=rgba(color,230),outline=(111,56,39,130),width=2)
    draw.polygon([(x-5,y-r*.84),(x+3,y-r*1.14),(x+13,y-r*1.11),(x+8,y-r*.80)],fill=(68,100,63,248))
    if glow:
        for eye_x in (x-r*.3,x+r*.3):
            draw.polygon(star_points(eye_x,y-r*.12,r*.10,3,.7),fill=(255,223,139,235))
        draw.arc((x-r*.31,y-r*.09,x+r*.31,y+r*.38),10,160,fill=(255,222,149,240),width=4)


def leaf(draw, x, y, r, color, angle=0):
    draw.polygon(star_points(x,y,r,5,.50,angle),fill=rgba(color,215),outline=(80,43,32,70))
    dx,dy=math.cos(angle),math.sin(angle)
    draw.line((x-r*dx*.5,y-r*dy*.5,x+r*dx*.65,y+r*dy*.65),fill=(255,217,154,125),width=2)


def snowflake(draw,x,y,r,color=(233,242,255),opacity=155):
    for angle in (0,math.pi/3,2*math.pi/3):
        dx,dy=r*math.cos(angle),r*math.sin(angle)
        draw.line((x-dx,y-dy,x+dx,y+dy),fill=rgba(color,opacity),width=max(2,int(r/8)))


def firework(draw,x,y,r,color,rng,intensity=210):
    for k in range(22):
        a=k*math.tau/22
        length=r*rng.uniform(.69,1.0)
        ix,iy=x+r*.20*math.cos(a),y+r*.20*math.sin(a)
        ox,oy=x+length*math.cos(a),y+length*math.sin(a)
        draw.line((ix,iy,ox,oy),fill=rgba(color,intensity),width=max(2,round(r/35)))
        draw.ellipse((ox-2,oy-2,ox+2,oy+2),fill=(255,240,211,210))


def bat(draw,x,y,r,color=(36,28,63)):
    pts=[(x-r,y),(x-r*.71,y-r*.28),(x-r*.36,y-r*.13),
         (x-r*.19,y-r*.41),(x,y-r*.18),(x+r*.19,y-r*.41),
         (x+r*.36,y-r*.13),(x+r*.71,y-r*.28),(x+r,y),
         (x+r*.68,y+r*.27),(x+r*.40,y+r*.12),(x+r*.11,y+r*.24),
         (x,y+r*.12),(x-r*.11,y+r*.24),(x-r*.40,y+r*.12),(x-r*.68,y+r*.27)]
    draw.polygon(pts,fill=rgba(color,210))


def easter_egg(draw,x,y,r,color,accent):
    draw.ellipse((x-r*.75,y-r,x+r*.75,y+r),fill=rgba(color,235),outline=(253,240,218,145),width=2)
    draw.arc((x-r*.55,y-r*.3,x+r*.55,y+r*.35),0,180,fill=rgba(accent,245),width=max(3,int(r*.11)))
    for k in (-.35,0,.35):
        draw.ellipse((x+k*r-3,y+r*.28-3,x+k*r+3,y+r*.28+3),fill=(255,255,255,175))


def composition(base_path,event,state,phase,wide):
    with Image.open(base_path) as im:
        image=im.convert("RGB")
    target_w,target_h=SIZES["wide" if wide else "square"]
    w,h=image.size
    target_ratio=target_w/target_h
    if w/h>target_ratio:
        crop_w=round(h*target_ratio)
        image=image.crop(((w-crop_w)//2,0,(w+crop_w)//2,h))
    else:
        crop_h=round(w/target_ratio)
        top=round((h-crop_h)*.38)
        image=image.crop((0,top,w,top+crop_h))
    image=image.resize((target_w,target_h),Image.Resampling.LANCZOS)
    e=(event+state+phase+str(wide)).encode()
    rng=random.Random(int.from_bytes(hashlib.sha256(e).digest()[:8],"big"))
    primary,secondary=EVENTS[event][1:]
    night=phase=="night"
    quiet=phase=="day"
    alpha=145 if state in ("heavy","storm","fog") else 205
    decorations=Image.new("RGBA",(target_w,target_h),(0,0,0,0))
    d=ImageDraw.Draw(decorations,"RGBA")
    W,H=target_w,target_h
    # Floating light motes, small enough to avoid obscuring weather readings.
    for _ in range(36 if night else 22):
        x,y=rng.uniform(.03,.97)*W,rng.uniform(.06,.94)*H
        if .24*W < x < .72*W and .17*H < y < .87*H: continue
        radius=rng.uniform(.8,2.5)*(1.2 if night else 1)
        d.ellipse((x-radius,y-radius,x+radius,y+radius),
                  fill=rgba(primary if rng.random()>.4 else secondary,rng.randrange(45,135)))
    # Holiday treatments: lively foreground around the perimeter, clear center.
    if event in ("july4","newyear"):
        palette=[primary,secondary,(250,245,222)] if event=="july4" else [primary,(255,228,175),(175,196,237)]
        for bx,by,mult in [(.85,.23,.63),(.93,.64,.34),(.13,.16,.28)]:
            c=rng.choice(palette)
            firework(d,W*bx,H*by,min(W,H)*.20*mult,c,rng,175 if quiet else 235)
        for i in range(13):
            x=W*(.012+i*.081)
            y=H*(.035+.018*math.sin(i))
            color=palette[i%len(palette)]
            d.polygon([(x-15,y),(x+15,y),(x,y+29)],fill=rgba(color,135 if quiet else 194))
        if event=="newyear":
            for _ in range(32):
                x=rng.choice([rng.uniform(0,.23),rng.uniform(.75,1)])*W
                y=rng.random()*H
                a=rng.uniform(0,math.tau);length=rng.uniform(7,18)
                d.line((x,y,x+math.cos(a)*length,y+math.sin(a)*length),
                       fill=rgba(rng.choice(palette),180),width=rng.choice([2,3,4]))
    elif event=="christmas":
        # Evergreen garlands, red ornaments, warm fairy lights.
        for side in (0,1):
            bx=W*(.05 if side==0 else .95)
            for i in range(17):
                y=H*i/16
                x=bx+math.sin(i*.8)*(W*.027)
                size=min(W,H)*rng.uniform(.029,.051)
                pts=[(x,y-size),(x-size*.9,y+size*.6),(x+size*.9,y+size*.6)]
                d.polygon(pts,fill=(42,115,74,165))
                d.line((x,y-size,x,y+size*.7),fill=(158,175,93,145),width=2)
            for i in range(8):
                y=H*(.06+i*.115)
                bulb= (245,208,121) if i%2 else (249,97,98)
                d.ellipse((bx-6,y-6,bx+6,y+6),fill=rgba(bulb,240))
        for i in range(6):
            x=W*(.08+i*.15)
            d.line((x,H*.012,x,H*.056),fill=(233,210,167,145),width=2)
            d.ellipse((x-7,H*.05,x+7,H*.08),fill=rgba(primary if i%2==0 else (239,210,116),195))
        for _ in range(13):
            x,y=rng.uniform(.05,.98)*W,rng.uniform(.10,.98)*H
            if x<W*.27 or x>W*.73: snowflake(d,x,y,rng.uniform(5,16),opacity=alpha)
    elif event=="easter":
        for x,y,c in [(W*.08,H*.82,primary),(W*.90,H*.79,secondary),(W*.93,H*.92,(211,174,235)),(W*.04,H*.94,(231,213,120))]:
            easter_egg(d,x,y,min(W,H)*.060,c,rng.choice([primary,secondary]))
        for _ in range(21):
            x=rng.choice([rng.uniform(.01,.25),rng.uniform(.78,.99)])*W
            y=rng.uniform(.08,.97)*H
            flower(d,x,y,rng.uniform(5,13),rng.choice([primary,secondary,(249,228,189)]))
        for i in range(13):
            x=W*(i/12)
            d.arc((x-15,H*.015,x+15,H*.06),0,180,fill=rgba(primary,100),width=2)
    elif event=="thanksgiving":
        for k in range(25):
            x=rng.choice([rng.uniform(0,.20),rng.uniform(.79,.99)])*W
            y=rng.uniform(.05,.98)*H
            leaf(d,x,y,min(W,H)*rng.uniform(.015,.044),
                 rng.choice([(220,137,69),(196,76,46),(239,178,85),(167,111,56)]),
                 rng.uniform(0,math.tau))
        for x,c in [(W*.10,(216,124,64)),(W*.91,(231,152,75))]:
            pumpkin(d,x,H*.90,min(W,H)*.067,c)
    elif event=="halloween":
        for bx,by,r in [(.84,.15,.09),(.94,.47,.05),(.10,.33,.054)]:
            bat(d,W*bx,H*by,min(W,H)*r)
        pumpkin(d,W*.89,H*.83,min(W,H)*.095,glow=True)
        pumpkin(d,W*.07,H*.91,min(W,H)*.065,color=(196,115,51),glow=True)
        for x,y in [(.89,.16),(.12,.17),(.93,.62)]:
            star=star_points(W*x,H*y,min(W,H)*.015,4,.38)
            d.polygon(star,fill=(219,195,251,160))
        # Mist remains transparent so actual rain/fog/nightscape stays readable.
    elif event=="memorial":
        # Restrained flags and poppies, not fireworks.
        for side in (.06,.93):
            x=W*side
            d.line((x,H*.12,x,H*.8),fill=(220,220,210,174),width=3)
            for i in range(5):
                y=H*(.16+i*.025)
                color=(194,63,73) if i%2==0 else (241,236,223)
                d.polygon([(x,y),(x+W*.09,y+5),(x+W*.09,y+H*.025),(x,y+H*.018)],
                          fill=rgba(color,170))
            d.rectangle((x,H*.155,x+W*.035,H*.215),fill=(50,88,157,183))
        for x in (.10,.88):
            flower(d,x*W,H*.87,min(W,H)*.06,(196,57,69),(35,30,44))
        for i in range(6):
            x=W*(.11+i*.15);y=H*(.03+.012*math.sin(i*2))
            d.polygon(star_points(x,y,6),fill=(246,233,207,130))
    elif event=="labor":
        # Last summer light: striped bunting, picnic/kite accents.
        for i in range(15):
            x=W*(i/14)
            y=H*(.04+.02*math.sin(i/2))
            color=[primary,(233,103,93),secondary,(251,222,151)][i%4]
            d.polygon([(x-13,y),(x+13,y),(x,y+22)],fill=rgba(color,172))
        x,y=W*.87,H*.46
        d.polygon([(x,y-45),(x+30,y),(x,y+45),(x-30,y)],fill=(255,216,131,175),
                  outline=(248,245,215,195),width=2)
        d.line((x,y+45,W*.94,H*.90),fill=(244,236,216,120),width=2)
        for i in range(5):
            flower(d,W*(.075 if i%2 else .925),H*(.55+.07*i),9,primary)
    elif event in ("birthday_a","birthday_b"):
        colors=[primary,secondary,(252,207,114),(181,162,224)] if event=="birthday_a" else [primary,secondary,(255,222,121),(178,151,243)]
        for i in range(8):
            side=.08 if i%2==0 else .91
            x=W*(side+rng.uniform(-.033,.034))
            y=H*(.20+.14*(i//2)+rng.uniform(-.035,.035))
            balloon(d,x,y,min(W,H)*rng.uniform(.035,.052),colors[i%4],rng)
        for i in range(28):
            x=rng.choice([rng.uniform(.01,.24),rng.uniform(.76,.98)])*W
            y=rng.uniform(.02,.95)*H
            a=rng.uniform(0,math.tau)
            d.polygon(star_points(x,y,rng.uniform(3,9),4,.42,a),
                      fill=rgba(rng.choice(colors),rng.randint(105,190)))

    if phase!="day":
        # Warm bulbs and sparkles add a twilight/night festive atmosphere.
        glow=Image.new("RGBA",(W,H),(0,0,0,0))
        gd=ImageDraw.Draw(glow,"RGBA")
        for k in range(15):
            x=rng.choice([rng.uniform(.01,.20),rng.uniform(.81,.99)])*W
            y=rng.uniform(.04,.95)*H
            rad=rng.uniform(7,18)
            gd.ellipse((x-rad,y-rad,x+rad,y+rad),fill=rgba(primary,80))
        glow=glow.filter(ImageFilter.GaussianBlur(12))
        decorations=Image.alpha_composite(glow,decorations)
    scene=Image.alpha_composite(image.convert("RGBA"),decorations).convert("RGB")
    return scene


def generate(images):
    images=Path(images)
    expected=0
    for key,(season,_,__) in EVENTS.items():
        for state in STATES:
            for phase in PHASES:
                for size in ("square","wide"):
                    wide=size=="wide"
                    source=images / (f"{season}_{state}_{phase}" + ("_wide.jpg" if wide else ".jpg"))
                    if not source.exists():
                        raise FileNotFoundError(f"Missing base weather art: {source}")
                    result=composition(source,key,state,phase,wide)
                    filename=f"holiday_{key}_{state}_{phase}" + ("_wide.jpg" if wide else ".jpg")
                    result.save(images/filename,"JPEG",quality=79,optimize=True,progressive=True)
                    expected+=1
    assert expected==480
    return expected


if __name__=="__main__":
    import sys
    count=generate(sys.argv[1])
    print(f"Generated {count} dedicated seasonal holiday scene variants (1:1 and 2:1)")
