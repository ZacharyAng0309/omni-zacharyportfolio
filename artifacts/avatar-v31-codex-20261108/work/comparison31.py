from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
root=Path(__file__).resolve().parents[1]
sheet=Image.new('RGB',(1180,460),'#eeedeb');draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',25);small=ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf',18)
draw.text((20,12),'Previous blink · v30',font=font,fill='#222')
draw.text((610,12),'Protected hairline · v31',font=font,fill='#222')
for col,label in enumerate(['baseline','candidate']):
    im=Image.open(root/f'work/face31-{label}-blink.png').convert('RGB')
    im=im.crop((160,320,740,700)).resize((550,360),Image.Resampling.LANCZOS)
    sheet.paste(im,(20+590*col,55))
draw.text((20,430),'Blender renders from exported models. Shared face/hair seam motion during blink: 2.79 mm → 0 mm.',font=small,fill='#333')
sheet.save(root/'outputs/avatar-v31-blink-comparison.jpg',quality=95)
