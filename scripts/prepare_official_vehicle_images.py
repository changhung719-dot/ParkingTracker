from pathlib import Path
from PIL import Image, ImageEnhance

root = Path('ParkingLocationPayload/app/src/main/res/drawable')
root.mkdir(parents=True, exist_ok=True)

for stem in ('car_seltos', 'car_g90'):
    for suffix in ('.png', '.jpg', '.jpeg', '.webp'):
        p = root / f'{stem}{suffix}'
        if p.exists():
            p.unlink()


def crop_ratio(src_path: str, ratios: tuple[float, float, float, float], out_path: Path, max_width: int = 900) -> None:
    image = Image.open(src_path).convert('RGB')
    w, h = image.size
    left, top, right, bottom = ratios
    crop = image.crop((round(w * left), round(h * top), round(w * right), round(h * bottom)))
    if crop.width > max_width:
        out_h = round(crop.height * max_width / crop.width)
        crop = crop.resize((max_width, out_h), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.08)
    crop = ImageEnhance.Contrast(crop).enhance(1.04)
    crop.save(out_path, 'WEBP', quality=91, method=6)


# Wikimedia Commons photo of a white Kia Seltos, already tightly side-cropped.
crop_ratio(
    'official_vehicle_images/seltos_official.jpg',
    (0.01, 0.08, 0.99, 0.94),
    root / 'car_seltos.webp',
)

# Wikimedia Commons photo of a current-generation black Genesis G90 RS4.
crop_ratio(
    'official_vehicle_images/g90_official.jpg',
    (0.00, 0.16, 1.00, 0.91),
    root / 'car_g90.webp',
)

credits = root.parent.parent / 'assets' / 'vehicle_photo_credits.txt'
credits.parent.mkdir(parents=True, exist_ok=True)
credits.write_text(
    'Vehicle photo credits\n'
    'Kia Seltos: White KIA Seltos (Side) (cropped).jpg, Benespit / Democfest, CC BY-SA 4.0, Wikimedia Commons.\n'
    'Genesis G90: Genesis G90 RS4 Maui Black (29).jpg, Damian B Oh, CC BY-SA 4.0, Wikimedia Commons.\n'
    'Images were cropped and resized for the application UI.\n',
    encoding='utf-8',
)
