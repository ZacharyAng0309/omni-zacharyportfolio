from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
sheet=Image.new('RGB',(1100,1200),'#eeedeb');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
draw.text((20,12),'Previous finger rig · v27',font=font,fill='#222')
draw.text((565,12),'Fitted joints and weights · v28',font=font,fill='#222')
for row,(curl,title) in enumerate([('0.35','Moderate curl'),('0.60','Stronger curl stress check')]):
    y=55+row*550;draw.text((20,y),title,font=small,fill='#333')
    for col,version in enumerate([27,28]):
        im=Image.open(root/f'work/hand-v{version}-{curl}-front.png').convert('RGB').resize((525,525),Image.Resampling.LANCZOS)
        sheet.paste(im,(20+545*col,y+25))
draw.text((20,1160),'Exported GLBs rendered in Blender. Finger surface geometry is unchanged; fused areas still need repair.',font=small,fill='#333')
sheet.save(root/'outputs/avatar-v28-finger-comparison.jpg',quality=95)
