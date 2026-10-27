# Seasonal Weather

A free, small-format iPhone weather widget that combines a live local forecast with seasonal scenery. Built with [Scriptable](https://scriptable.app/) and [Open-Meteo](https://open-meteo.com/).

- Current GPS location, temperature, and weather condition
- Next three hourly forecasts
- 96 local weather backgrounds: 4 seasons × 8 conditions × 3 lighting modes
- Tap the widget to open Apple Weather via its unofficial `weather://` URL scheme
- A responsive, interactive public landing page

## Website publication status

**The repository is configured for GitHub Pages deployment.** It needs one remaining file: `seasonal-weather-site.zip`.

The full website ZIP was prepared in the original ChatGPT conversation and contains the landing page, all 96 images, the widget script, and the iPhone installation package. To finish publishing:

1. Download `seasonal-weather-site.zip` from the ChatGPT conversation.
2. Open this GitHub repository → **Add file → Upload files**.
3. Upload the ZIP **without extracting it**, into the repository root. Keep the filename `seasonal-weather-site.zip`, then commit to `main`.
4. Open **Settings → Pages → Build and deployment → Source** and select **GitHub Actions**.
5. Open **Actions → Publish Seasonal Weather** and verify the deployment succeeds. If needed, select **Run workflow**.

The site URL will be: **https://matthnj15-pixel.github.io/Seasonal-Weather/**

The workflow at `.github/workflows/deploy.yml` extracts and deploys the actual site, including its background images and downloadable install kit. Updating the ZIP triggers another deployment.

## Privacy and compatibility

The public landing page previews simulated conditions and does not access the visitor's location. The installed widget obtains GPS coordinates with Scriptable permission and sends coordinates to Open-Meteo to retrieve forecasts. Cache files are stored on the iPhone. The project contains no hardcoded hometown, personal credentials, or API keys.

The link to Apple Weather uses an unofficial iOS URL scheme, so its behavior may vary with iOS version. iOS also controls when widgets refresh.

## Attribution and licensing

Forecast data: [Open-Meteo](https://open-meteo.com/), subject to its attribution and noncommercial-use terms. This is an independent project and is not affiliated with Apple or Scriptable. The packaged website includes a code license; the publisher should confirm artwork licensing before public redistribution.
