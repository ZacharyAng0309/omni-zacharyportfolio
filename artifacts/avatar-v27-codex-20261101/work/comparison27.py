from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
sheet = Image.new('RGB', (1000, 1366), '#eeeeec')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 24)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 18)
draw.text((16, 10), 'Previous rig and poses · v26', font=font, fill='#222222')
draw.text((512, 10), 'Refined rig and fitted poses · v27', font=font, fill='#222222')
for row, (label, title) in enumerate([
    ('glasses_adjust', 'Adjust glasses'),
    ('inspect_tablet', 'Tablet hand position'),
    ('keynote_present', 'Present'),
]):
    y = 50 + row * 428
    draw.text((16, y), title, font=small, fill='#333333')
    for column, version in enumerate((26, 27)):
        picture = Image.open(root / f'work/rig{version}-{label}.png').convert('RGB')
        picture = picture.crop((65, 65, 685, 565)).resize((480, 387), Image.Resampling.LANCZOS)
        sheet.paste(picture, (16 + column * 496, y + 28))
draw.text((16, 1340), 'Rendered in Blender from the exported models. Matching cameras and lighting.', font=small, fill='#333333')
sheet.save(root / 'outputs/avatar-v27-gesture-comparison.jpg', quality=95)
