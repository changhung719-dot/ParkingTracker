from pathlib import Path
from PIL import Image, ImageEnhance

root = Path('ParkingLocationPayload/app/src/main/res/drawable')
root.mkdir(parents=True, exist_ok=True)

for stem in ('car_seltos', 'car_g90'):
    for suffix in ('.png', '.jpg', '.jpeg', '.webp'):
        p = root / f'{stem}{suffix}'
        if p.exists():
            p.unlink()


def crop_resize(src_path: str, crop_box: tuple[int, int, int, int], out_path: Path, max_width: int = 900) -> None:
    image = Image.open(src_path).convert('RGB')
    crop = image.crop(crop_box)
    if crop.width > max_width:
        height = round(crop.height * max_width / crop.width)
        crop = crop.resize((max_width, height), Image.Resampling.LANCZOS)
    crop = ImageEnhance.Sharpness(crop).enhance(1.08)
    crop = ImageEnhance.Contrast(crop).enhance(1.03)
    crop.save(out_path, 'WEBP', quality=91, method=6)


# Official Kia current Seltos hero image: crop around the entire vehicle.
crop_resize(
    'official_vehicle_images/seltos_official.jpg',
    (165, 92, 850, 470),
    root / 'car_seltos.webp',
)

# Official Genesis G90 passenger-side profile: crop around the entire sedan.
crop_resize(
    'official_vehicle_images/g90_official.webp',
    (75, 80, 1055, 450),
    root / 'car_g90.webp',
)
