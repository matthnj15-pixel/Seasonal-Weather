# Seasonal Weather

A free, small-format iPhone weather widget that combines a live local forecast with seasonal scenery. Built with [Scriptable](https://scriptable.app/) and [Open-Meteo](https://open-meteo.com/).

- Current GPS location, temperature, and weather condition
- Next three hourly forecasts
- 96 local weather backgrounds: 4 seasons × 8 conditions × 3 lighting modes
- Tap the widget to open Apple Weather via its unofficial `weather://` URL scheme
- A responsive, interactive public landing page

## Website publication status

**The website package is uploaded and the GitHub Actions workflow is configured.** To publish, enable GitHub Pages at **Settings → Pages → Build and deployment → Source: GitHub Actions**, then rerun the **Publish Seasonal Weather** workflow in Actions.

The GitHub Actions workflow extracts the uploaded ZIP, applies the latest approved landing page copy and styling from `site-overrides/`, and deploys it automatically.

The site URL will be: **https://matthnj15-pixel.github.io/Seasonal-Weather/**

The workflow at `.github/workflows/deploy.yml` extracts and deploys the actual site, including its background images and downloadable install kit. Commits to `main` trigger another deployment.

## Privacy and compatibility

The public landing page previews simulated conditions and does not access the visitor's location. The installed widget obtains GPS coordinates with Scriptable permission and sends coordinates to Open-Meteo to retrieve forecasts. Cache files are stored on the iPhone. The project contains no hardcoded hometown, personal credentials, or API keys.

The link to Apple Weather uses an unofficial iOS URL scheme, so its behavior may vary with iOS version. iOS also controls when widgets refresh.

## Attribution and licensing

Forecast data: [Open-Meteo](https://open-meteo.com/), subject to its attribution and noncommercial-use terms. This is an independent project and is not affiliated with Apple or Scriptable. The packaged website includes a code license; the publisher should confirm artwork licensing before public redistribution.
