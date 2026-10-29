# Seasonal Weather

A free Scriptable weather widget for iPhone with seasonal scenery, your current GPS location, live conditions, and an hourly forecast. The **same script automatically supports two Home Screen sizes**:

| Widget size | Current weather | Future forecast | Artwork |
| --- | --- | --- | --- |
| Small (1:1) | Location, temperature, condition | Next **3** hours | Square seasonal scenes |
| Medium (2:1) | Location, temperature, condition | Next **5** hours | Wide seasonal scenes |

## Install

1. Visit [the Seasonal Weather website](https://matthnj15-pixel.github.io/Seasonal-Weather/) and download the **complete widget kit**.
2. Unzip the kit on your iPhone and open **Scriptable**.
3. Create one script called `Seasonal Hourly Weather`, and paste the included `Seasonal_Hourly_Weather.js`.
4. Run the script once and select the extracted `SeasonalWeatherArt` folder when prompted. Grant location permission.
5. Add a **small** and/or **medium** Scriptable widget to the Home Screen. Select **the same script** for either one.

The widget detects `config.widgetFamily` and renders the appropriate layout. The Scriptable app also offers a small/medium preview picker. You don't need two scripts or duplicate weather requests.

**Existing small-widget users:** The new code works with the original 96-image pack. If you haven't imported the wide images yet, the medium widget crops the installed square image as a fallback. Import the new art pack to use the 96 dedicated wide-format images.

## Weather and backgrounds

- Four seasons × eight weather scenes × day/twilight/night = **96 conditions**, each with square and 2:1 artwork, **192 background files** in the installer.
- Weather data is fetched from [Open-Meteo](https://open-meteo.com/) using on-device GPS coordinates.
- Tapping the widget attempts to launch Apple Weather through the unofficial `weather://` URL scheme. This isn't guaranteed on all iOS versions.
- iOS controls widget refresh timing; the script requests a refresh after 30 minutes and caches recent data on the device.

## Source and publishing

The single canonical Scriptable source is [Seasonal_Hourly_Weather.js](Seasonal_Hourly_Weather.js). The website's download script and ZIP installation kit are generated from this file, and the 2:1 images are derived from the original scenery during publishing.

This repository's [GitHub Actions workflow](.github/workflows/deploy.yml) assembles the site and installer and deploys to [GitHub Pages](https://matthnj15-pixel.github.io/Seasonal-Weather/).

## Privacy and licensing

The website uses example data and does not request location. The installed widget requests location permission through Scriptable, caches the result locally, and sends coordinates to Open-Meteo to fetch local weather. There are no hardcoded hometowns, user credentials, or API keys in the code.

Forecast data attribution: Open-Meteo, subject to its current licensing/attribution terms. Independent Scriptable project; not affiliated with Apple.
