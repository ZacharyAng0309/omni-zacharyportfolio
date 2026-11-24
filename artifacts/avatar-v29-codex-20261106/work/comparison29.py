from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
sheet=Image.new('RGB',(1100,1200),'#eeedeb');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
draw.text((20,12),'Previous palm surface · v28',font=font,fill='#222')
draw.text((565,12),'Refined palm surface · v29',font=font,fill='#222')
for row,(curl,title) in enumerate([('0.00','Left hand at rest'),('0.35','Left hand with moderate curl')]):
    y=55+row*550;draw.text((20,y),title,font=small,fill='#333')
    for col,version in enumerate([28,29]):
        im=Image.open(root/f'work/hand-v{version}-left-{curl}-outer.png').convert('RGB').resize((525,525),Image.Resampling.LANCZOS)
        sheet.paste(im,(20+545*col,y+25))
draw.text((20,1160),'Exported GLBs rendered in Blender. Local palm relaxation; cuff seam retained. Fused finger web remains.',font=small,fill='#333')
sheet.save(root/'outputs/avatar-v29-palm-comparison.jpg',quality=95)
