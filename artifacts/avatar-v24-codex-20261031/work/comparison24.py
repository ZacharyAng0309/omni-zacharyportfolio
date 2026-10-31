from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out = Path(__file__).resolve().parents[1] / 'outputs'
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
sheet = Image.new('RGB', (872, 974), '#eeeeec')
draw = ImageDraw.Draw(sheet)
draw.text((16, 14), 'Before · v23', font=font, fill='#222222')
draw.text((452, 14), 'Repaired · v24', font=font, fill='#222222')
for row, sign in enumerate((-1, 1)):
    y = 58 + row * 448
    for col, version in enumerate((23, 24)):
        image = Image.open(out / f'rim-v{version}-{sign}-1.png').convert('RGB')
        sheet.paste(image, (16 + col * 436, y))
draw.text((16, 944), 'Matching front-view cameras and lighting. Upper rim beneath each glasses arm.', font=small, fill='#333333')
sheet.save(out / 'avatar-v24-ear-comparison.jpg', quality=95)
