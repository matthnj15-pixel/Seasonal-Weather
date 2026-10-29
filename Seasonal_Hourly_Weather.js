// SEASONAL HOURLY WEATHER
// Scriptable adaptive small + medium Home Screen widget
// Four seasons x eight weather conditions x day / twilight / night
// Forecast data: Open-Meteo. Location: your device GPS.
// Artwork pack: SeasonalWeatherArt (import once in Scriptable).

const SETTINGS = {
  forecastHours: 3,
  refreshMinutes: 30,
  contentWidth: 138,
  topPadding: 8,
  bottomPadding: 8,

  // Fine-tune these Scriptable POINT values, not screenshot pixels.
  locationToTemp: 0,
  tempToCondition: 5,
  conditionToForecast: 3,
  hourToIcon: 3,
  iconToDegrees: 3,

  cityFont: 12,
  currentTempFont: 43,
  conditionFont: 11,
  hourFont: 9,
  hourlyTempFont: 14,
  topIcon: 17,
  hourIcon: 18,

  // Optional artwork testing IN THE APP: set null to use real weather.
  // e.g. testSeason: "winter", testCondition: "snow", testPhase: "day"
  testSeason: null,
  testCondition: null,
  testPhase: null
};

const C = {
  white: new Color("#FFFFFF"),
  secondary: new Color("#FFFFFF", 0.90),
  muted: new Color("#FFFFFF", 0.83),
  sun: new Color("#FFD348"),
  cloud: new Color("#F9FBFF"),
  rain: new Color("#B9E8FF")
};

const fm = FileManager.local();
const root = fm.documentsDirectory();
const artDir = fm.joinPath(root, "SeasonalWeatherArt");
const cacheDir = fm.joinPath(root, "SeasonalWeatherCache");
if (!fm.fileExists(cacheDir)) fm.createDirectory(cacheDir, true);
const locationFile = fm.joinPath(cacheDir, "location.json");
const weatherFile = fm.joinPath(cacheDir, "weather.json");

function readJSON(file) {
  try {
    return fm.fileExists(file) ? JSON.parse(fm.readString(file)) : null;
  } catch (e) { return null; }
}
function saveJSON(file, data) {
  try { fm.writeString(file, JSON.stringify(data)); } catch (e) {}
}

// ONE-TIME ARTWORK IMPORT
// Download and unzip the kit in Files, then select the extracted
// SeasonalWeatherArt folder. The images are copied into Scriptable's
// local storage, so widget refreshes never need to download artwork.
function artworkInstalled() {
  try {
    return fm.fileExists(artDir) &&
      fm.listContents(artDir).filter(name => name.endsWith(".jpg") && !name.endsWith("_wide.jpg")).length >= 96;
  } catch (e) { return false; }
}

async function importArtwork() {
  if (config.runsInWidget || artworkInstalled()) return;
  const alert = new Alert();
  alert.title = "Install seasonal backgrounds";
  alert.message = "Unzip the Weather Kit in Files. Choose the SeasonalWeatherArt folder when prompted. You only do this once.";
  alert.addAction("Choose artwork folder");
  alert.addCancelAction("Preview without artwork");
  const choice = await alert.presentAlert();
  if (choice !== 0) return;

  try {
    const folder = await DocumentPicker.openFolder();
    if (!folder) return;
    if (!fm.fileExists(artDir)) fm.createDirectory(artDir, true);

    // Files selected through DocumentPicker can be on the device or iCloud.
    // Try both FileManagers when reading each source file.
    let cloud = null;
    try { cloud = FileManager.iCloud(); } catch (e) {}
    const seasons = ["spring", "summer", "fall", "winter"];
    const states = ["sunny", "partly", "cloudy", "rain", "heavy", "storm", "snow", "fog"];
    const phases = ["day", "twilight", "night"];
    let copied = 0;
    let failed = 0;

    for (const season of seasons) {
      for (const state of states) {
        for (const phase of phases) {
          const name = `${season}_${state}_${phase}.jpg`;
          const src = fm.joinPath(folder, name);
          const dst = fm.joinPath(artDir, name);
          try {
            let raw = null;
            try { raw = fm.read(src); } catch (e) {}
            if (!raw && cloud) {
              try {
                await cloud.downloadFileFromiCloud(src);
                raw = cloud.read(src);
              } catch (e) {}
            }
            if (!raw) throw new Error("Cannot read file");
            fm.write(dst, raw);
            copied++;

            // The same art pack may contain 2:1 landscape variants.
            // These are optional, because older 96-image packs still work.
            const wideName = name.replace(".jpg", "_wide.jpg");
            const wideSrc = fm.joinPath(folder, wideName);
            const wideDst = fm.joinPath(artDir, wideName);
            try {
              let wideBytes = null;
              try { wideBytes = fm.read(wideSrc); } catch (e) {}
              if (!wideBytes && cloud) {
                try {
                  await cloud.downloadFileFromiCloud(wideSrc);
                  wideBytes = cloud.read(wideSrc);
                } catch (e) {}
              }
              if (wideBytes) fm.write(wideDst, wideBytes);
            } catch (e) {}
          } catch (e) { failed++; }
        }
      }
    }

    const result = new Alert();
    result.title = copied === 96 ? "Artwork installed" : "Artwork import result";
    result.message = `${copied} of 96 backgrounds imported.${failed ? " Reopen the extracted SeasonalWeatherArt folder to retry missing files." : " The widget is ready."}`;
    result.addAction("OK");
    await result.presentAlert();
  } catch (e) {
    console.warn("Artwork import cancelled or failed: " + e);
  }
}

// GPS LOCATION. Never hard-code Lewistown or any other city.
async function getLocation() {
  const old = readJSON(locationFile);
  try {
    Location.setAccuracyToHundredMeters();
    const fix = await Location.current();
    const nearOld = old &&
      Math.abs(fix.latitude - old.latitude) < 0.012 &&
      Math.abs(fix.longitude - old.longitude) < 0.012;

    let city = nearOld && old.city ? old.city : "Current Location";
    if (!nearOld) {
      try {
        const places = await Location.reverseGeocode(fix.latitude, fix.longitude);
        const place = places && places[0];
        if (place) {
          city = place.locality || place.subLocality ||
            place.name || place.administrativeArea || city;
        }
      } catch (e) {}
    }

    const loc = { latitude: fix.latitude, longitude: fix.longitude,
      city: city, recordedAt: Date.now(), source: "gps" };
    saveJSON(locationFile, loc);
    return loc;
  } catch (e) {
    // Only show last-known weather if a fairly recent fix exists.
    if (old && old.recordedAt &&
      Date.now() - old.recordedAt < 48 * 60 * 60 * 1000) {
      old.source = "cached";
      return old;
    }
    return null;
  }
}

// LIVE FORECAST
async function getWeather(loc) {
  if (!loc) return null;
  const query = [
    `latitude=${loc.latitude}`,
    `longitude=${loc.longitude}`,
    "current=temperature_2m,weather_code,is_day",
    "hourly=temperature_2m,weather_code,is_day",
    "daily=sunrise,sunset",
    "temperature_unit=fahrenheit",
    "timeformat=unixtime",
    "timezone=auto",
    "forecast_days=2"
  ].join("&");

  try {
    const req = new Request(`https://api.open-meteo.com/v1/forecast?${query}`);
    req.timeoutInterval = 12;
    const data = await req.loadJSON();
    if (!data.current || !data.hourly || !Array.isArray(data.hourly.time))
      throw new Error("Incomplete forecast response");
    saveJSON(weatherFile, { data: data, lat: loc.latitude,
      lon: loc.longitude, fetched: Date.now() });
    return data;
  } catch (e) {
    const saved = readJSON(weatherFile);
    const sameArea = saved &&
      Math.abs(saved.lat - loc.latitude) < 0.035 &&
      Math.abs(saved.lon - loc.longitude) < 0.035;
    if (sameArea && saved.data &&
      Date.now() - saved.fetched < 4 * 60 * 60 * 1000) return saved.data;
    console.warn("Weather unavailable: " + e);
    return null;
  }
}

// SEASON AND SOLAR PHASE FROM THE FORECAST LOCATION
function seasonAt(loc, data) {
  const utcOffset = data ? (data.utc_offset_seconds || 0) : 0;
  const localMonth = new Date(Date.now() + utcOffset * 1000).getUTCMonth() + 1;
  const month = loc && loc.latitude < 0 ? ((localMonth + 5) % 12) + 1 : localMonth;
  if (month >= 3 && month <= 5) return "spring";
  if (month >= 6 && month <= 8) return "summer";
  if (month >= 9 && month <= 11) return "fall";
  return "winter";
}

function solarPhase(data) {
  if (!data) return "day";
  const sunrise = data.daily && data.daily.sunrise && data.daily.sunrise[0];
  const sunset = data.daily && data.daily.sunset && data.daily.sunset[0];
  const now = Date.now() / 1000;
  if (sunrise && Math.abs(now - sunrise) <= 40 * 60) return "twilight";
  if (sunset && Math.abs(now - sunset) <= 40 * 60) return "twilight";
  return data.current.is_day === 0 ? "night" : "day";
}

// Official Open-Meteo WMO weather codes.
function weatherStyle(code) {
  if (code === 0 || code === 1) return "sunny";
  if (code === 2) return "partly";
  if (code === 3) return "cloudy";
  if (code === 45 || code === 48) return "fog";
  if (code >= 95) return "storm";
  if (code >= 71 && code <= 77) return "snow";
  if (code === 85 || code === 86) return "snow";
  if (code === 65 || code === 82) return "heavy";
  if (code >= 51 && code <= 67) return "rain";
  if (code >= 80 && code <= 81) return "rain";
  return "cloudy";
}

function labelFor(code, day) {
  if (code === 0) return day ? "Sunny" : "Clear";
  if (code === 1) return day ? "Mostly Sunny" : "Mostly Clear";
  if (code === 2) return "Partly Cloudy";
  if (code === 3) return "Cloudy";
  if (code === 45 || code === 48) return "Foggy";
  if (code >= 95) return "Thunderstorms";
  if (code === 65 || code === 82) return "Heavy Rain";
  if (code === 66 || code === 67) return "Freezing Rain";
  if (code >= 71 && code <= 77) return "Snow";
  if (code === 85 || code === 86) return "Snow Showers";
  if (code >= 51 && code <= 57) return "Drizzle";
  if (code >= 61 && code <= 63) return "Rain";
  if (code >= 80 && code <= 81) return "Showers";
  return "Conditions";
}

function weatherSymbol(code, day) {
  const style = weatherStyle(code);
  if (style === "sunny") return [day ? "sun.max.fill" : "moon.stars.fill", day ? C.sun : C.cloud];
  if (style === "partly") return [day ? "cloud.sun.fill" : "cloud.moon.fill", C.cloud];
  if (style === "cloudy") return ["cloud.fill", C.cloud];
  if (style === "fog") return ["cloud.fog.fill", C.cloud];
  if (style === "storm") return ["cloud.bolt.rain.fill", C.cloud];
  if (style === "snow") return ["cloud.snow.fill", C.cloud];
  if (style === "heavy") return ["cloud.heavyrain.fill", C.rain];
  if (code >= 51 && code <= 57) return ["cloud.drizzle.fill", C.rain];
  return ["cloud.rain.fill", C.rain];
}

function addIcon(stack, code, day, points) {
  const style = weatherSymbol(code, day);
  const sf = SFSymbol.named(style[0]) || SFSymbol.named("cloud.fill");
  sf.applyFont(Font.systemFont(points));
  const icon = stack.addImage(sf.image);
  icon.imageSize = new Size(points, points);
  icon.applyFittingContentMode();
  icon.tintColor = style[1];
  return icon;
}

function addText(stack, value, font, color) {
  const item = stack.addText(String(value));
  item.font = font;
  item.textColor = color;
  item.lineLimit = 1;
  item.minimumScaleFactor = 0.68;
  // Keep white text legible over bright skies and snow.
  item.shadowColor = new Color("#000000", 0.65);
  item.shadowRadius = 2;
  item.shadowOffset = new Point(0, 1);
  return item;
}

function nextHours(data, count) {
  if (!data) return [];
  const result = [];
  const h = data.hourly;
  const now = Math.floor(Date.now() / 1000);
  for (let i = 0; i < h.time.length; i++) {
    if (h.time[i] <= now || !Number.isFinite(h.temperature_2m[i])) continue;
    result.push({ time: h.time[i], temp: h.temperature_2m[i],
      code: h.weather_code[i], day: h.is_day ? h.is_day[i] === 1 : true });
    if (result.length === (count || SETTINGS.forecastHours)) break;
  }
  return result;
}

function hourLabel(unix, utcOffset) {
  const h = new Date((unix + utcOffset) * 1000).getUTCHours();
  return `${h % 12 || 12} ${h < 12 ? "AM" : "PM"}`;
}

function applyBackground(widget, loc, weather) {
  const day = !weather || weather.current.is_day !== 0;
  const season = !config.runsInWidget && SETTINGS.testSeason
    ? SETTINGS.testSeason : seasonAt(loc, weather);
  const state = !config.runsInWidget && SETTINGS.testCondition
    ? SETTINGS.testCondition : weather ? weatherStyle(weather.current.weather_code) : "cloudy";
  const phase = !config.runsInWidget && SETTINGS.testPhase
    ? SETTINGS.testPhase : solarPhase(weather);
  const filename = `${season}_${state}_${phase}.jpg`;
  const file = fm.joinPath(artDir, filename);

  try {
    if (fm.fileExists(file)) {
      const picture = fm.readImage(file);
      if (picture) {
        widget.backgroundImage = picture;
        return filename;
      }
    }
  } catch (e) {}

  // Fallback works even before importing the art pack.
  const gradient = new LinearGradient();
  gradient.colors = day
    ? [new Color("#2C6194"), new Color("#72A1CF")]
    : [new Color("#18385F"), new Color("#426B9A")];
  gradient.locations = [0, 1];
  gradient.startPoint = new Point(0, 0);
  gradient.endPoint = new Point(1, 1);
  widget.backgroundGradient = gradient;
  return "gradient";
}

// The V4 centered, compact layout, deliberately unchanged.
function buildWidget(loc, weather) {
  const w = new ListWidget();
  w.setPadding(SETTINGS.topPadding, 0, SETTINGS.bottomPadding, 0);
  w.spacing = 0;
  w.url = "weather://"; // Tap anywhere to open Apple Weather (unofficial URL scheme).
  w.refreshAfterDate = new Date(Date.now() + SETTINGS.refreshMinutes * 60000);
  applyBackground(w, loc, weather);

  w.addSpacer();
  const centerRow = w.addStack();
  centerRow.layoutHorizontally();
  centerRow.spacing = 0;
  centerRow.addSpacer();
  const body = centerRow.addStack();
  body.layoutVertically();
  body.spacing = 0;
  body.size = new Size(SETTINGS.contentWidth, 0);
  centerRow.addSpacer();
  w.addSpacer();

  const header = body.addStack();
  header.layoutHorizontally();
  header.centerAlignContent();
  header.spacing = 0;
  header.size = new Size(SETTINGS.contentWidth, 0);
  const city = loc ? (loc.source === "cached" ? "~" + loc.city : loc.city) : "Location unavailable";
  addText(header, city, Font.mediumSystemFont(SETTINGS.cityFont), C.white);
  header.addSpacer(3);
  if (weather) {
    header.addSpacer();
    addIcon(header, weather.current.weather_code, weather.current.is_day !== 0, SETTINGS.topIcon);
  }

  body.addSpacer(SETTINGS.locationToTemp);
  addText(body, weather ? `${Math.round(weather.current.temperature_2m)}°` : "--°",
    Font.lightSystemFont(SETTINGS.currentTempFont), C.white);
  body.addSpacer(SETTINGS.tempToCondition);
  addText(body, weather ? labelFor(weather.current.weather_code, weather.current.is_day !== 0) : "Weather unavailable",
    Font.regularSystemFont(SETTINGS.conditionFont), C.secondary);
  body.addSpacer(SETTINGS.conditionToForecast);

  if (weather) {
    const hours = nextHours(weather);
    const row = body.addStack();
    row.layoutHorizontally();
    row.spacing = 0;
    row.size = new Size(SETTINGS.contentWidth, 0);
    row.addSpacer();
    for (const hour of hours) {
      const col = row.addStack();
      col.layoutVertically();
      col.centerAlignContent();
      col.spacing = 0;
      col.size = new Size(36, 0);
      addText(col, hourLabel(hour.time, weather.utc_offset_seconds || 0),
        Font.mediumSystemFont(SETTINGS.hourFont), C.muted);
      col.addSpacer(SETTINGS.hourToIcon);
      addIcon(col, hour.code, hour.day, SETTINGS.hourIcon);
      col.addSpacer(SETTINGS.iconToDegrees);
      addText(col, `${Math.round(hour.temp)}°`, Font.mediumSystemFont(SETTINGS.hourlyTempFont), C.white);
      row.addSpacer();
    }
  }
  return w;
}


// ---------------------------------------------------------------
// MEDIUM 2:1 VARIANT
// Uses the same script, weather, cache, and seasonal artwork.
// The Home Screen widget size is supplied by Scriptable.
// ---------------------------------------------------------------

function mediumArtwork(source) {
  // Legacy square art becomes a wide aspect-fill image on the fly.
  // An installed _wide.jpg file takes priority over this fallback.
  const canvas = new DrawContext();
  const width = 960;
  const height = 480;
  canvas.size = new Size(width, height);
  canvas.opaque = true;
  canvas.respectScreenScale = false;
  const originalWidth = source.size.width;
  const originalHeight = source.size.height;
  const scale = Math.max(width / originalWidth, height / originalHeight);
  const drawWidth = originalWidth * scale;
  const drawHeight = originalHeight * scale;
  canvas.drawImageInRect(source, new Rect(
    (width - drawWidth) / 2,
    (height - drawHeight) / 2,
    drawWidth, drawHeight
  ));
  return canvas.getImage();
}

function applyMediumBackground(widget, loc, weather) {
  const season = !config.runsInWidget && SETTINGS.testSeason
    ? SETTINGS.testSeason : seasonAt(loc, weather);
  const state = !config.runsInWidget && SETTINGS.testCondition
    ? SETTINGS.testCondition
    : weather ? weatherStyle(weather.current.weather_code) : "cloudy";
  const phase = !config.runsInWidget && SETTINGS.testPhase
    ? SETTINGS.testPhase : solarPhase(weather);
  const base = season + "_" + state + "_" + phase;
  const widePath = fm.joinPath(artDir, base + "_wide.jpg");
  const regularPath = fm.joinPath(artDir, base + ".jpg");
  try {
    if (fm.fileExists(widePath)) {
      widget.backgroundImage = fm.readImage(widePath);
      return;
    }
    if (fm.fileExists(regularPath)) {
      const original = fm.readImage(regularPath);
      try {
        widget.backgroundImage = mediumArtwork(original);
      } catch (e) {
        widget.backgroundImage = original;
      }
      return;
    }
  } catch (e) {}
  // The normal weather-dependent gradient is still available offline.
  applyBackground(widget, loc, weather);
}

function buildMediumWidget(loc, weather) {
  const w = new ListWidget();
  w.setPadding(8, 15, 8, 15);
  w.spacing = 0;
  w.url = "weather://";
  w.refreshAfterDate = new Date(Date.now() + SETTINGS.refreshMinutes * 60000);
  applyMediumBackground(w, loc, weather);

  const daytime = !weather || weather.current.is_day !== 0;

  // Balanced vertical padding comes from the two equal flexible spacers.
  w.addSpacer();
  const top = w.addStack();
  top.layoutHorizontally();
  top.centerAlignContent();
  addText(top, loc
    ? (loc.source === "cached" ? "~" + loc.city : loc.city)
    : "Location unavailable", Font.mediumSystemFont(12), C.white);
  top.addSpacer();
  if (weather) {
    addIcon(top, weather.current.weather_code, daytime, 18);
  }

  // The temperature and condition remain grouped, rather than
  // allowing a flexible spacer to separate them.
  w.addSpacer(0);
  addText(w, weather
    ? String(Math.round(weather.current.temperature_2m)) + "°"
    : "--°", Font.lightSystemFont(40), C.white);
  w.addSpacer(0);
  addText(w, weather
    ? labelFor(weather.current.weather_code, daytime)
    : "Weather unavailable", Font.regularSystemFont(11), C.secondary);

  w.addSpacer(5);

  if (weather) {
    const hours = nextHours(weather, 5);
    const row = w.addStack();
    row.layoutHorizontally();
    row.centerAlignContent();
    row.spacing = 0;
    row.backgroundColor = new Color("#061322", 0.24);
    row.cornerRadius = 12;
    row.setPadding(5, 4, 5, 4);
    row.addSpacer();

    for (const hour of hours) {
      const column = row.addStack();
      column.layoutVertically();
      column.centerAlignContent();
      column.spacing = 0;
      // Fixed equal-sized forecast columns; flexible spaces use
      // all remaining width without shifting the forecast left.
      column.size = new Size(45, 0);
      addText(column,
        hourLabel(hour.time, weather.utc_offset_seconds || 0),
        Font.mediumSystemFont(9), C.muted);
      column.addSpacer(3);
      addIcon(column, hour.code, hour.day, 17);
      column.addSpacer(3);
      addText(column, String(Math.round(hour.temp)) + "°",
        Font.mediumSystemFont(14), C.white);
      row.addSpacer();
    }
  }
  w.addSpacer();
  return w;
}

async function previewSize() {
  const alert = new Alert();
  alert.title = "Preview Seasonal Weather";
  alert.message = "One script supports both Home Screen widget sizes.";
  alert.addAction("Small · 3 hours");
  alert.addAction("Medium · 5 hours");
  const selected = await alert.presentAlert();
  return selected === 1 ? "medium" : "small";
}

async function main() {
  if (!config.runsInWidget) await importArtwork();
  const loc = await getLocation();
  const weather = await getWeather(loc);
  // config.widgetFamily is "small" or "medium" in a Home Screen widget.
  // In Scriptable itself, choose a size for the preview.
  const family = config.runsInWidget ? config.widgetFamily : await previewSize();
  const w = family === "medium"
    ? buildMediumWidget(loc, weather)
    : buildWidget(loc, weather);
  Script.setWidget(w);
  if (!config.runsInWidget) {
    if (family === "medium") await w.presentMedium();
    else await w.presentSmall();
  }
  Script.complete();
}

await main();