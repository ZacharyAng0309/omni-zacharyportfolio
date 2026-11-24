from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

root = Path(__file__).resolve().parents[1]
out = root / 'outputs'
sheet = Image.new('RGB', (1000, 864), '#eeeeec')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 26)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 17)
draw.text((16, 12), 'Before · v24', font=font, fill='#222222')
draw.text((512, 12), 'Refined hair · v25', font=font, fill='#222222')
for row, (view, crop) in enumerate([
    ('front', (120, 30, 600, 410)),
    ('left', (90, 30, 570, 410)),
]):
    for column, version in enumerate((24, 25)):
        prefix = 'earfit' if version == 24 else 'hairfit'
        picture = Image.open(out / f'{prefix}-v{version}-{view}.png').convert('RGB').crop(crop)
        sheet.paste(picture, (16 + column * 496, 58 + row * 396))
draw.text((16, 838), 'Matching cameras and lighting. Images rendered from the exported GLB models.', font=small, fill='#333333')
sheet.save(out / 'avatar-v25-hair-comparison.jpg', quality=95)
