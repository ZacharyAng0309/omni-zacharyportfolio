from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
sheet = Image.new('RGB', (1000, 1050), '#eeeeec')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 26)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
draw.text((16, 12), 'Before · v25', font=font, fill='#222222')
draw.text((512, 12), 'Repaired materials · v26', font=font, fill='#222222')
rows = [
    ['outputs/hairfit-v25-right.png', 'outputs/materialfit-v26-right.png'],
    ['work/full25-hand.png', 'outputs/full26-hand.png'],
]
for row, paths in enumerate(rows):
    for column, path in enumerate(paths):
        image = Image.open(root / path).convert('RGB').resize((480, 480), Image.Resampling.LANCZOS)
        sheet.paste(image, (16 + column * 496, 58 + row * 490))
draw.text((16, 1027), 'Matching cameras and lighting. Neck and cuff color transitions from exported models.', font=small, fill='#333333')
sheet.save(root / 'outputs/avatar-v26-material-comparison.jpg', quality=95)
