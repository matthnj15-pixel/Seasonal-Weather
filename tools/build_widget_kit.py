#!/usr/bin/env python3
"""Build the single-script installation kit and 2:1 artwork for GitHub Pages."""
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from PIL import Image
from generate_holiday_art import generate
import sys
import os
from install_rendered_art import integrate

site = Path(sys.argv[1])
source = Path("Seasonal_Hourly_Weather.js")
images = site / "assets" / "backgrounds"
downloads = site / "downloads"
kit_path = downloads / "Seasonal_Weather_Widget_Kit.zip"
square_art = sorted(p for p in images.glob("*.jpg") if not p.stem.endswith("_wide"))

if len(square_art) != 96:
    raise RuntimeError(f"Expected 96 seasonal scenes, found {len(square_art)}")

# A landscape crop of each scene maintains the season and conditions
# without distorting the original scene. Slightly favor the sky.
for path in square_art:
    with Image.open(path) as original:
        image = original.convert("RGB")
    width, height = image.size
    target_ratio = 2.0
    if width / height > target_ratio:
        crop_width = round(height * target_ratio)
        x = (width - crop_width) // 2
        crop = image.crop((x, 0, x + crop_width, height))
    else:
        crop_height = round(width / target_ratio)
        y = round((height - crop_height) * 0.38)
        crop = image.crop((0, y, width, y + crop_height))
    wide = crop.resize((960, 480), Image.Resampling.LANCZOS)
    wide.save(path.with_name(path.stem + "_wide.jpg"), "JPEG", quality=85, optimize=True)

holiday_count = generate(images)
assert holiday_count == 480

# Independently AI-rendered art takes priority over the old procedural output.
# Full release mode refuses incomplete master packs rather than silently
# shipping placeholder images as completed photorealistic artwork.
rendered = Path('artwork/photoreal')
if rendered.is_dir():
    strict = os.environ.get('AI_ART_STRICT', 'false').lower() == 'true'
    installed, missing = integrate(rendered, images, strict=strict)
    if installed < 480:
        print(f'Warning: {480-installed} scenes still use legacy artwork. Not V3 release-ready.')
elif os.environ.get('AI_ART_STRICT', 'false').lower() == 'true':
    raise RuntimeError('Photoreal artwork pack not present; release blocked')
assert len(list(images.glob("*.jpg"))) == 672

js = source.read_bytes()
(downloads / "Seasonal_Hourly_Weather.js").write_bytes(js)

readme = """SEASONAL WEATHER | ONE SCRIPT, TWO WIDGET SIZES

1. Download and unzip the kit using Files on your iPhone.
2. Copy Seasonal_Hourly_Weather.js into one new Scriptable script.
3. Run the script in Scriptable and select the extracted SeasonalWeatherArt
   folder when asked to install backgrounds. Grant location permission.
4. Add Scriptable Home Screen widgets in small and/or medium sizes.
5. Select the SAME Seasonal Hourly Weather script in both widgets.

Small: current weather + next 3 hours.
Medium: current weather + next 5 hours.
The script detects widget size automatically, and previews both sizes
when launched inside Scriptable.

The package includes 96 standard weather scenes and 240 special-edition
weather scenes, each in square and 2:1 wide format: 672 images total.

Holiday editions: Fourth of July, Christmas, New Year's Eve and Day, Easter,
Thanksgiving, Halloween, Memorial Day, Labor Day, October 6 birthday,
and July 9 birthday.

Set SETTINGS.specialEditions=false to opt out. Change the two entries in
SETTINGS.specialDates for your own birthdays. Holiday activation uses
the local date of the weather location; other days use regular backgrounds.

To upgrade an earlier install, open the new script inside Scriptable,
choose Import / update artwork, and select the extracted SeasonalWeatherArt
folder. The old seasonal art remains supported as a fallback.

The weather:// tap link for Apple Weather is unofficial.
Location is obtained on-device; weather data comes from Open-Meteo.
"""
(downloads / "README_Seasonal_Weather.txt").write_text(readme, encoding="utf-8")
temp_zip = kit_path.with_suffix(".building.zip")
with ZipFile(temp_zip, "w", ZIP_DEFLATED, compresslevel=7) as zipped:
    zipped.writestr("Seasonal_Hourly_Weather.js", js)
    zipped.writestr("README_Seasonal_Weather.txt", readme)
    for path in sorted(images.glob("*.jpg")):
        zipped.write(path, "SeasonalWeatherArt/" + path.name)
temp_zip.replace(kit_path)

with ZipFile(kit_path) as check:
    names = check.namelist()
    if len([n for n in names if n.startswith("SeasonalWeatherArt/") and n.endswith(".jpg")]) != 672:
        raise RuntimeError("Installation kit did not contain all 672 images")
    if check.read("Seasonal_Hourly_Weather.js") != js:
        raise RuntimeError("Website script and installer script are different")
# Verify representative holiday artwork in both aspect ratios.
for suffix, expected_ratio in ((".jpg", 1.0), ("_wide.jpg", 2.0)):
    sample = images / ("holiday_christmas_sunny_day" + suffix)
    with Image.open(sample) as image:
        ratio = image.size[0] / image.size[1]
        assert abs(ratio - expected_ratio) < .01, (sample, ratio)
print(f"Built adaptive widget kit with 672 images (480 special): {kit_path.stat().st_size:,} bytes")
