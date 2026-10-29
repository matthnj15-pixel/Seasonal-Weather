#!/usr/bin/env python3
"""Holiday Editions V2: cinematic, full-scene, people-free weather artwork.

Every scene starts with the matching season/weather/lighting photograph, then
builds a physically integrated foreground, hero props, material shading, haze,
occlusion, reflections and illumination. Wide scenes are composed separately,
not cropped from the square holiday output. No faces or human silhouettes.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageEnhance, ImageFilter
import hashlib
import math
import random
import sys

EVENTS = {
    "july4": "summer",
    "christmas": "winter",
    "newyear": "winter",
    "easter": "spring",
    "thanksgiving": "fall",
    "halloween": "fall",
    "memorial": "spring",
    "labor": "summer",
    "birthday_a": "fall",
    "birthday_b": "summer",
}
WEATHER = ("sunny", "partly", "cloudy", "rain", "heavy", "storm", "snow", "fog")
PHASES = ("day", "twilight", "night")
SIZES = {"square": (720,720), "wide": (960,480)}

def rgba(rgb,a=255): return tuple(int(v) for v in rgb[:3])+(int(a),)
def clamp(v,a=0,b=255): return max(a,min(b,int(v)))
def mix(a,b,t): return tuple(clamp(a[i]*(1-t)+b[i]*t) for i in range(3))

def points(cx,cy,r,fold=5,inside=.43,turn=-math.pi/2):
    return [(cx+math.cos(turn+i*math.pi/fold)*(r if i%2==0 else r*inside),
             cy+math.sin(turn+i*math.pi/fold)*(r if i%2==0 else r*inside))
            for i in range(fold*2)]

def softglow(scene, spots):
    W,H=scene.size
    layer=Image.new("RGBA",(W,H))
    d=ImageDraw.Draw(layer,"RGBA")
    for x,y,r,c,alpha in spots:
        d.ellipse((x-r,y-r,x+r,y+r),fill=rgba(c,alpha))
    blur=layer.filter(ImageFilter.GaussianBlur(max(7,int(H*.017))))
    return Image.alpha_composite(scene,blur)

def ground(scene,holiday,state,phase,rng):
    """Actual opaque terrain/porch/lawn below decoration, not floating stickers."""
    W,H=scene.size
    d=ImageDraw.Draw(scene,"RGBA")
    snow=state=="snow" or holiday=="christmas"
    if snow: palette=[(231,242,251),(210,226,242),(185,210,234)]
    elif holiday in ("halloween","thanksgiving","birthday_a"):
        palette=[(93,69,50),(68,52,42),(44,43,36)]
    elif holiday=="easter":palette=[(80,145,68),(65,120,63),(50,93,52)]
    elif holiday in ("july4","newyear"):palette=[(35,64,83),(25,45,65),(21,37,53)]
    else:palette=[(96,108,71),(63,91,65),(43,72,54)]
    iswide=W>H
    horizon=.81 if iswide else .82
    if holiday in ("halloween","easter"):horizon=.74 if iswide else .76
    y0=int(H*horizon)
    # Irregular horizon and solid shaded foreground form the physical floor.
    coords=[(0,H),(0,y0)]
    for i in range(1,32):
        x=W*i/31
        wave=H*(.008*math.sin(i*.71)+.006*math.sin(i*1.93))
        coords.append((x,y0+wave))
    coords.append((W,H))
    d.polygon(coords,fill=rgba(palette[0],238))
    for y in range(y0,H):
        t=(y-y0)/max(1,H-y0)
        col=mix(palette[0],palette[2],t)
        d.line((0,y,W,y),fill=rgba(col,round(25+130*t)),width=1)
    # Ground carries physical grain, small blades / gravel / snow granules.
    for _ in range(700 if iswide else 900):
        x=rng.randrange(W);y=rng.randrange(y0,H)
        t=(y-y0)/max(1,H-y0)
        r=rng.uniform(.3,2.2)*(1+t)
        c=mix(palette[1],palette[0],rng.random())
        if snow:
            d.ellipse((x-r,y-r/2,x+r,y+r/2),fill=rgba((245,250,255),rng.randrange(36,115)))
        elif holiday=="easter" or holiday=="labor":
            d.line((x,y,x+rng.uniform(-3,3),y-rng.uniform(2,10)*t),
                   fill=rgba((117,158,82),rng.randrange(40,170)),width=1)
        else:
            d.ellipse((x-r,y-r/2,x+r,y+r/2),fill=rgba(c,rng.randrange(15,78)))
    return y0

def physical_shadow(draw,x,y,rx,ry,night=False):
    draw.ellipse((x-rx,y-ry*.55,x+rx,y+ry*.55),fill=(7,11,18,135 if night else 100))
    draw.ellipse((x-rx*.7,y-ry*.25,x+rx*.7,y+ry*.25),fill=(7,11,18,105))

def rendered_balloon(draw,x,y,r,base,rng):
    # Rounded translucent latex with shaded rim, highlight and tied string.
    draw.line([(x,y+r*.83),(x+8,y+r*3.8)],fill=(239,235,221,175),width=2)
    for i in range(13,0,-1):
        f=i/13
        col=mix(base,(15,19,38),.35*f)
        draw.ellipse((x-r*.75*f,y-r*1.13*f,x+r*.75*f,y+r*.83*f),
                     fill=rgba(col,220 if i>2 else 255))
    draw.ellipse((x-r*.42,y-r*.87,x-r*.16,y-r*.47),fill=(255,255,255,105))
    draw.polygon([(x-5,y+r*.77),(x+5,y+r*.77),(x,y+r)],fill=rgba(base,242))

def tree(draw,x,ground_y,height,rng,glows,night,scene_scale=1):
    W=draw.im.size[0];H=draw.im.size[1]
    spread=height*.44
    physical_shadow(draw,x,ground_y,spread*.70,height*.065,night)
    draw.polygon([(x-height*.045,ground_y),(x+height*.045,ground_y),
                  (x+height*.018,ground_y-height*.25),(x-height*.018,ground_y-height*.25)],
                 fill=(72,51,39,250))
    # Dense overlapping boughs with fine evergreen needles and realistic highlights.
    branches=[]
    for layer in range(27):
        t=layer/26
        yy=ground_y-height*(1-t*.92)
        half=height*(.047+.40*t)
        branches.append((yy,half))
        shade=int(14+30*t)
        col=(18+shade//3,58+shade,33+shade//2)
        draw.polygon([(x,yy-height*.06),(x-half,yy+height*.079),
                      (x-half*.58,yy+height*.047),
                      (x,yy+height*.099),(x+half*.59,yy+height*.047),
                      (x+half,yy+height*.079)],fill=rgba(col,248))
        for k in range(15):
            xx=x+rng.uniform(-.98,.98)*half
            dy=rng.uniform(.005,.085)*height
            needle=(39+rng.randrange(25),99+rng.randrange(45),43+rng.randrange(30))
            draw.line((xx,yy+dy*.10,xx+rng.uniform(-5,5),yy+dy),
                      fill=rgba(needle,145),width=1)
    draw.polygon(points(x,ground_y-height*.99,height*.050,5,.55),fill=(255,224,138,255))
    glows.append((x,ground_y-height*.99,height*.090,(255,224,119),130))
    # Christmas ornaments and strings in the pine, brighter at night.
    palette=[(235,67,64),(243,193,93),(219,229,225),(111,180,218)]
    for k in range(80):
        yy=ground_y-height*rng.uniform(.08,.91)
        t=(ground_y-yy)/height
        half=height*.39*(1-t)
        xx=x+rng.uniform(-.95,.95)*half
        if abs(xx-x)<height*.018 and k%3:continue
        r=height*rng.uniform(.004,.012)
        col=palette[k%len(palette)]
        if k%3==0:
            glows.append((xx,yy,r*4,col,85 if night else 38))
        draw.ellipse((xx-r,yy-r,xx+r,yy+r),fill=rgba(col,245),
                     outline=(255,242,191,100),width=1)
        draw.ellipse((xx-r*.5,yy-r*.65,xx-r*.1,yy-r*.17),fill=(255,255,255,160))

def gift(draw,x,y,w,h,c):
    physical_shadow(draw,x,y,w*.60,h*.09)
    draw.polygon([(x-w/2,y-h),(x+w/2,y-h),(x+w/2,y),(x-w/2,y)],
                 fill=rgba(c,255),outline=(31,39,54,110),width=2)
    draw.polygon([(x-w/2,y-h),(x,y-h-h*.15),(x+w/2,y-h),(x,y-h+h*.12)],
                 fill=rgba(mix(c,(252,250,234),.18),255))
    draw.rectangle((x-w*.09,y-h,x+w*.09,y),fill=(241,197,103,245))
    draw.rectangle((x-w/2,y-h*.62,x+w/2,y-h*.45),fill=(241,197,103,238))

def pumpkin(draw,x,y,r,glows,night,face=True):
    physical_shadow(draw,x,y,r*1.10,r*.19,night)
    for j in range(9):
        dx=(j-4)*r*.18
        rr=r*math.sqrt(max(.16,1-(dx/(r*.96))**2))
        col=(225-int(abs(j-4)*11),111-int(abs(j-4)*5),44)
        draw.ellipse((x+dx-rr*.45,y-r*.88,x+dx+rr*.45,y),
                     fill=rgba(col,255),outline=(112,58,37,135),width=2)
    draw.polygon([(x-r*.05,y-r*.88),(x+r*.08,y-r*1.17),
                  (x+r*.24,y-r*1.14),(x+r*.12,y-r*.78)],fill=(58,91,52,255))
    if face:
        hot=(255,220,116,255) if night else (86,42,27,250)
        for dx in (-.32,.29):
            draw.polygon([(x+r*(dx-.15),y-r*.58),(x+r*(dx+.13),y-r*.58),
                          (x+r*dx,y-r*.37)],fill=hot)
        draw.polygon([(x-r*.10,y-r*.34),(x+r*.10,y-r*.34),(x,y-r*.20)],fill=hot)
        draw.arc((x-r*.41,y-r*.48,x+r*.41,y-r*.05),10,170,fill=hot,width=max(3,int(r*.10)))
        if night:glows.append((x,y-r*.40,r*1.28,(250,134,41),115))

def egg(draw,x,y,r,c,rng):
    physical_shadow(draw,x,y,r*.74,r*.11)
    # Gradated eggshell as many filled nested ovals for sculpted shading.
    for i in range(13,0,-1):
        f=i/13
        shade=mix(c,(28,43,41),.30*f)
        draw.ellipse((x-r*.72*f,y-r*1.18*f,x+r*.72*f,y+r*.62*f),fill=rgba(shade,255))
    draw.ellipse((x-r*.36,y-r*.98,x-r*.07,y-r*.66),fill=(255,255,255,117))
    stripe=mix(c,(255,245,219),.76)
    for p in (-.45,-.12,.28):
        yy=y+r*p
        width=r*.55*math.sqrt(max(.05,1-((yy-y)/(r*1.15))**2))
        draw.arc((x-width,yy-r*.11,x+width,yy+r*.11),0,180,fill=rgba(stripe,224),width=max(2,int(r*.075)))
    for dx,dy in [(-.25,-.3),(.28,.16)]:
        a=r*.065
        draw.ellipse((x+r*dx-a,y+r*dy-a,x+r*dx+a,y+r*dy+a),fill=rgba((253,240,208),235))

def flower(draw,x,y,r,color,glows=None):
    for j in range(7):
        a=math.tau*j/7
        xx=x+math.cos(a)*r*.65;yy=y+math.sin(a)*r*.65
        draw.ellipse((xx-r*.45,yy-r*.45,xx+r*.45,yy+r*.45),fill=rgba(color,238))
    draw.ellipse((x-r*.28,y-r*.28,x+r*.28,y+r*.28),fill=(245,205,105,255))

def grave(draw,x,feet,w,h,night,rng):
    physical_shadow(draw,x,feet,w*.65,h*.06,night)
    shape=[(x-w*.5,feet),(x-w*.5,feet-h*.70),
           (x-w*.46,feet-h*.87),(x-w*.32,feet-h*.98),
           (x,feet-h*1.06),(x+w*.32,feet-h*.98),
           (x+w*.46,feet-h*.87),(x+w*.50,feet-h*.70),(x+w*.50,feet)]
    draw.polygon(shape,fill=(76,80,82,255),outline=(30,37,46,220),width=3)
    draw.line((x-w*.35,feet-h*.7,x-w*.30,feet-h*.94,x,feet-h*1.01),
              fill=(151,151,145,135),width=2)
    draw.arc((x-w*.19,feet-h*.77,x+w*.18,feet-h*.45),20,160,
             fill=(39,46,49,168),width=max(2,int(w*.045)))
    for i in range(20):
        xx=x+rng.uniform(-.38,.38)*w
        yy=feet-rng.uniform(.12,.72)*h
        draw.point((xx,yy),fill=(183,184,164,rng.randrange(55,160)))

def skyburst(core,glow,x,y,r,rng,palette,night):
    palette=list(palette)
    for k in range(60):
        a=(k+.1*rng.random())*math.tau/60
        size=r*rng.uniform(.58,1.22)
        x1=x+math.cos(a)*r*.12;y1=y+math.sin(a)*r*.12
        x2=x+math.cos(a)*size;y2=y+math.sin(a)*size
        color=palette[k%len(palette)]
        glow.line((x1,y1,x2,y2),fill=rgba(color,175 if night else 100),width=7)
        core.line((x1,y1,x2,y2),fill=rgba(color,250 if night else 190),width=2)
        core.ellipse((x2-2,y2-2,x2+2,y2+2),fill=(255,243,222,245))

def atmosphere(scene,event,state,phase,rng):
    W,H=scene.size
    # Keep weather photographic and add context in front of new objects.
    draw=ImageDraw.Draw(scene,"RGBA")
    if state in ("fog","heavy","storm"):
        fog=Image.new("RGBA",(W,H))
        fd=ImageDraw.Draw(fog,"RGBA")
        amount={"fog":80,"heavy":21,"storm":20}[state]
        for i in range(12):
            yy=H*(.43+i*.047)
            fd.ellipse((-W*.20,yy-H*.09,W*1.2,yy+H*.12),
                       fill=(183,193,208,int(amount*.20)))
        fog=fog.filter(ImageFilter.GaussianBlur(H*.04))
        scene=Image.alpha_composite(scene,fog)
        draw=ImageDraw.Draw(scene,"RGBA")
    if state in ("rain","heavy","storm"):
        count={"rain":135,"heavy":275,"storm":195}[state]
        for i in range(count):
            x=rng.uniform(0,W);y=rng.uniform(0,H)
            length=rng.uniform(8,20)*(1.6 if state=="heavy" else 1)
            draw.line((x,y,x-length*.29,y+length),
                      fill=(206,226,244,rng.randrange(58,145)),width=1)
    if state=="snow":
        for i in range(190):
            x=rng.uniform(0,W);y=rng.uniform(0,H);r=rng.uniform(.6,3.2)
            draw.ellipse((x-r,y-r,x+r,y+r),fill=(248,252,255,rng.randrange(130,245)))
    if state=="storm":
        x=W*.93
        draw.line([(x,H*.04),(x-W*.04,H*.24),(x-W*.02,H*.24),
                   (x-W*.065,H*.42)],fill=(216,229,249,100),width=2)
    return scene

def scene(base_path,event,state,phase,wide):
    W,H=SIZES["wide" if wide else "square"]
    rng=random.Random(int.from_bytes(hashlib.sha256(f"{event}-{state}-{phase}-{wide}".encode()).digest()[:8],"big"))
    with Image.open(base_path) as input_image:
        image=input_image.convert("RGB")
    iw,ih=image.size
    ratio=W/H
    # Compose holiday foreground on the original weather scene (never crop
    # finished holiday art), preserving normal sky and weather integrity.
    if iw/ih>ratio:
        cw=round(ih*ratio);image=image.crop(((iw-cw)//2,0,(iw+cw)//2,ih))
    else:
        ch=round(iw/ratio);top=round((ih-ch)*.35)
        image=image.crop((0,top,iw,top+ch))
    image=image.resize((W,H),Image.Resampling.LANCZOS)
    # Distinct film color grading, without flattening the sky/weather.
    image=ImageEnhance.Contrast(image).enhance(1.07)
    image=ImageEnhance.Color(image).enhance(1.09)
    scene=image.convert("RGBA")
    night=phase=="night"
    y0=ground(scene,event,state,phase,rng)
    d=ImageDraw.Draw(scene,"RGBA")
    glows=[]
    right=W*.82 if wide else W*.79
    left=W*.13 if wide else W*.15
    base=H*.94
    if event=="christmas":
        height=H*(.78 if wide else .66)
        tree(d,right,base,height,rng,glows,night)
        for x,y,w,h,c in [(right-height*.21,base,42,36,(189,54,65)),
                           (right+height*.23,base,38,29,(54,125,143)),
                           (right+height*.02,base,32,27,(224,191,107))]:
            gift(d,x,y,w*H/480,h*H/480,c)
        for i in range(5):
            x=W*(.08+i*.11) if wide else W*(.05+i*.16)
            yy=H*(.065+.01*math.sin(i))
            drawcol=(248,198,95) if i%2 else (225,68,75)
            glows.append((x,yy,H*.026,drawcol,120 if night else 40))
            d.ellipse((x-5,yy-5,x+5,yy+5),fill=rgba(drawcol,250))
    elif event in ("july4","newyear"):
        palette=[(240,70,76),(92,169,246),(252,240,214)] if event=="july4" else [(249,214,111),(251,236,185),(159,183,228)]
        fireworks=Image.new("RGBA",(W,H));fw=ImageDraw.Draw(fireworks,"RGBA")
        bloom=Image.new("RGBA",(W,H));bl=ImageDraw.Draw(bloom,"RGBA")
        locations=[(.84,.20,.25),(.65,.26,.17),(.95,.46,.15),(.36,.10,.12)] if wide else [(.80,.20,.26),(.50,.12,.19),(.95,.50,.18)]
        for px,py,r in locations:
            skyburst(fw,bl,W*px,H*py,H*r,rng,palette,night)
        bloom=bloom.filter(ImageFilter.GaussianBlur(max(5,H*.014)))
        scene=Image.alpha_composite(scene,bloom)
        scene=Image.alpha_composite(scene,fireworks)
        d=ImageDraw.Draw(scene,"RGBA")
        # Visible sparkler fountains, grounded in landscape rather than held.
        for i in range(4):
            x=W*(.62+i*.105) if wide else W*(.25+i*.23)
            y=H*.91
            for k in range(30):
                a=rng.uniform(-2.90,-.25)
                rr=H*rng.uniform(.02,.18)
                color=rng.choice(palette)
                d.line((x,y,x+math.cos(a)*rr,y+math.sin(a)*rr),
                       fill=rgba(color,rng.randrange(145,245)),width=rng.choice([1,2]))
        if event=="newyear":
            # Distant midnight skyline, roofs softened by weather atmosphere.
            for i in range(16):
                x=W*(.57+i*.028) if wide else W*(.08+i*.055)
                h=H*rng.uniform(.07,.23);width=W*.026
                d.rectangle((x,y0-h,x+width,y0),fill=(28,39,58,245))
                for j in range(6):
                    px=x+4+(j%2)*7;py=y0-h+6+(j//2)*11
                    if py<y0-5:d.rectangle((px,py,px+2,py+3),fill=(235,200,131,205))
        else:
            for i in range(9):
                x=W*(.50+i*.05) if wide else W*(.07+i*.10)
                y=H*(.075+.014*math.sin(i))
                d.polygon([(x-12,y),(x+12,y),(x,y+22)],
                          fill=rgba(palette[i%len(palette)],235))
    elif event=="easter":
        # Low meadow camera angle: abundant eggs actually resting in grass.
        eggs=[(rng.uniform(.49,.96) if wide else rng.uniform(.05,.96),
               rng.uniform(.81,.98),rng.uniform(.038,.082)) for i in range(24)]
        eggs=sorted(eggs,key=lambda x:x[1])
        colors=[(238,137,163),(121,187,213),(241,205,102),(169,140,217),
                (155,215,162),(239,157,99)]
        for x,y,r in eggs:
            egg(d,W*x,H*y,H*r,rng.choice(colors),rng)
        for i in range(76):
            x=rng.uniform(0,W);y=rng.uniform(y0,H)
            if wide and .09*W<x<.53*W:continue
            r=rng.uniform(2.8,8.5)*(y/H)
            flower(d,x,y,r,rng.choice([(250,220,220),(231,189,226),(245,239,182),(239,245,249)]))
        for i in range(320):
            x=rng.uniform(0,W);y=rng.uniform(y0,H)
            d.line((x,y,x+rng.uniform(-5,5),y-rng.uniform(5,16)),
                   fill=(81,141,68,rng.randrange(110,210)),width=1)
    elif event=="halloween":
        # Deep layered graveyard with stone arches, exposed branches and
        # oversized internally lit carved jack-o'-lanterns.
        for i in range(8):
            x=W*(.52+i*.066) if wide else W*(.08+i*.115)
            grave(d,x,H*(.80+.018*(i%3)),W*rng.uniform(.031,.05),H*rng.uniform(.15,.30),night,rng)
        for dx,dy,r in [(.83,.94,.115),(.97,.98,.072),(.62,.95,.068)] if wide else [(.78,.96,.13),(.96,.95,.095),(.11,.96,.078)]:
            pumpkin(d,W*dx,H*dy,H*r,glows,night)
        # Ghosts are nonhuman will-o'-the-wisp wisps, not figures or faces.
        for x,y in [(W*.87,H*.35),(W*.70,H*.48)]:
            for j in range(3):
                rr=H*(.06+j*.025)
                d.arc((x-rr,y-rr,x+rr,y+rr),160+j*12,325+j*7,
                      fill=(211,234,250,55+j*10),width=5)
        # Twisted tree branches frame haunted scene.
        for x,side in [(W*.98,-1),(W*.58,1)] if wide else [(W*.98,-1),(W*.02,1)]:
            by=H*.80
            d.line((x,by,x+side*W*.04,H*.18),fill=(38,31,37,235),width=int(H*.025))
            for j in range(9):
                yy=H*(.20+j*.055)
                d.line((x+side*W*.03,yy,x+side*W*rng.uniform(.05,.21),yy-H*rng.uniform(.03,.12)),
                       fill=(44,34,40,225),width=rng.choice([3,5,7]))
    elif event=="thanksgiving":
        for x,y,r in [(.84,.96,.12),(.69,.95,.075),(.95,.98,.09)] if wide else [(.82,.97,.14),(.56,.95,.09),(.96,.98,.10)]:
            pumpkin(d,W*x,H*y,H*r,glows,night,False)
        for i in range(16):
            x=W*(.57+rng.random()*.42) if wide else W*rng.choice([rng.uniform(.03,.20),rng.uniform(.65,.99)])
            y=H*rng.uniform(.70,.95)
            col=rng.choice([(212,124,52),(177,72,48),(230,178,72)])
            d.polygon(points(x,y,H*rng.uniform(.017,.045),5,.46,rng.random()*6.28),
                      fill=rgba(col,245))
        # Porch lanterns and harvest baskets.
        for x in [W*.65,W*.96]:
            d.rounded_rectangle((x-H*.032,H*.73,x+H*.032,H*.88),radius=6,
                fill=(58,52,48,235),outline=(224,183,123,180),width=3)
            d.rectangle((x-H*.018,H*.75,x+H*.018,H*.86),fill=(247,196,111,235))
            glows.append((x,H*.80,H*.11,(250,192,94),115))
    elif event=="memorial":
        x=right;y=H*.96;w=H*.28;h=H*.35
        physical_shadow(d,x,y,w*.7,H*.04,night)
        d.polygon([(x-w*.55,y),(x-w*.46,y-h*.95),(x-w*.38,y-h*1.08),
                   (x+w*.38,y-h*1.08),(x+w*.46,y-h*.95),(x+w*.55,y)],
                  fill=(154,152,144,255),outline=(91,96,98,210),width=3)
        d.line((x-w*.25,y-h*.85,x+w*.22,y-h*.85),fill=(235,236,219,145),width=4)
        for j in range(4):
            fx=x+H*(j-1.7)*.24
            d.line((fx,H*.34,fx,H*.90),fill=(193,201,207,230),width=3)
            flagx=fx+H*.09
            d.polygon([(fx,H*.35),(flagx,H*.365),(flagx,H*.49),(fx,H*.475)],
                      fill=(248,239,215,235))
            for z in range(5):
                yy=H*(.37+z*.022)
                d.line((fx,yy,flagx,yy+3),fill=(195,65,66,240),width=3)
            d.rectangle((fx,H*.355,fx+H*.027,H*.405),fill=(52,88,151,255))
        for j in range(44):
            x=W*(rng.uniform(.55,.99) if wide else rng.random())
            y=H*rng.uniform(.83,.98)
            flower(d,x,y,H*rng.uniform(.006,.016),(192,44,54))
    elif event=="labor":
        # Empty late-summer picnic setting, no people or silhouettes.
        x=right;y=H*.95
        d.polygon([(x-H*.31,y-H*.14),(x+H*.26,y-H*.14),
                   (x+H*.38,y),(x-H*.36,y)],fill=(221,76,70,245))
        for i in range(9):
            px=x-H*.30+i*H*.075
            d.line((px,y-H*.13,px+H*.02,y),fill=(239,225,204,140),width=5)
        d.rounded_rectangle((x-H*.20,y-H*.24,x+H*.04,y-H*.10),radius=6,
                            fill=(150,110,65,240),outline=(230,185,118,200),width=3)
        for j in range(15):
            fx=W*(.49+j*.034) if wide else W*(.04+j*.064)
            d.polygon([(fx,H*.085),(fx+13,H*.08),(fx+7,H*.13)],
                      fill=rgba([(221,89,74),(244,215,118),(100,159,207)][j%3],225))
        for j in range(17):
            flower(d,W*(rng.uniform(.53,.99) if wide else rng.random()),
                   H*rng.uniform(.80,.97),H*rng.uniform(.008,.021),
                   rng.choice([(235,199,70),(241,225,149)]))
    elif event in ("birthday_a","birthday_b"):
        colors=[(221,157,98),(164,67,96),(249,220,142),(210,175,206)] if event=="birthday_a" else [(248,128,169),(105,208,208),(245,208,120),(177,153,234)]
        cake_x=right;cake_y=H*.95;cake_w=H*.34;cake_h=H*.15
        physical_shadow(d,cake_x,cake_y,cake_w*.65,H*.045,night)
        d.rounded_rectangle((cake_x-cake_w/2,cake_y-cake_h,cake_x+cake_w/2,cake_y),
                            radius=H*.024,fill=(246,225,208,255),outline=(169,112,112,220),width=3)
        d.arc((cake_x-cake_w*.44,cake_y-cake_h*.63,cake_x+cake_w*.44,cake_y-cake_h*.09),
              0,180,fill=rgba(colors[0],245),width=5)
        for i in range(6):
            px=cake_x+(i-2.5)*cake_w*.135
            d.line((px,cake_y-cake_h,px,cake_y-cake_h-H*.062),
                   fill=rgba(colors[i%len(colors)],255),width=3)
            d.polygon(points(px,cake_y-cake_h-H*.078,H*.013,5,.48),fill=(255,222,128,255))
            glows.append((px,cake_y-cake_h-H*.08,H*.05,(255,202,113),72))
        for i in range(15):
            x=W*(rng.uniform(.63,.97) if wide else rng.choice([rng.uniform(.02,.19),rng.uniform(.71,.98)]))
            y=H*rng.uniform(.20,.59)
            r=H*rng.uniform(.026,.049)
            rendered_balloon(d,x,y,r,colors[i%len(colors)],rng)
        for i in range(28):
            x=W*rng.random();y=H*rng.uniform(.04,.9)
            if wide and x<W*.52:continue
            c=rng.choice(colors)
            d.polygon(points(x,y,rng.uniform(3,9),4,.4,rng.random()*6.28),
                      fill=rgba(c,196))
    if glows:
        scene=softglow(scene,glows)
    return atmosphere(scene,event,state,phase,rng).convert("RGB")

def generate(images):
    images=Path(images)
    count=0
    for event,season in EVENTS.items():
        for state in WEATHER:
            for phase in PHASES:
                for format_name in SIZES:
                    wide=format_name=="wide"
                    source=images/(f"{season}_{state}_{phase}"+("_wide.jpg" if wide else ".jpg"))
                    if not source.exists():raise FileNotFoundError(source)
                    result=scene(source,event,state,phase,wide)
                    filename=f"holiday_{event}_{state}_{phase}"+("_wide.jpg" if wide else ".jpg")
                    result.save(images/filename,"JPEG",quality=84,optimize=True,progressive=True)
                    count+=1
    if count!=480:raise RuntimeError(f"Holiday scene count mismatch: {count}")
    print("Generated 480 cinematic, weather-aware, people-free holiday scenes")
    return count

if __name__=="__main__":
    print(generate(sys.argv[1]))
