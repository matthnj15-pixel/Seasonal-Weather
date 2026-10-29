// Preview the same Scriptable widget in either small or medium format.
(() => {
  "use strict";
  let size = "small";
  const cards = [
    document.getElementById("hero-widget"),
    document.getElementById("preview-widget")
  ].filter(Boolean);

  function extendForecast(card) {
    const forecast = card.querySelector(".forecast-grid");
    if (!forecast) return;
    const entries = Array.from(forecast.children);
    if (size === "small") {
      entries.slice(3).forEach(el => el.remove());
      return;
    }
    if (entries.length < 3) return;
    if (entries.length >= 5) return;

    const firstTemp = Number.parseInt(card.querySelector(".big-temp")?.textContent, 10) || 62;
    const icon = card.querySelector(".current-icon")?.textContent || "☀";
    ["3 PM", "4 PM"].forEach((time, i) => {
      const cell = document.createElement("div");
      cell.className = "forecast-hour";
      const hour = document.createElement("div");
      hour.className = "time";
      hour.textContent = time;
      const symbol = document.createElement("div");
      symbol.className = "symbol";
      symbol.textContent = icon;
      const temp = document.createElement("div");
      temp.className = "degrees";
      temp.textContent = String(firstTemp + 5 + i) + "°";
      cell.append(hour, symbol, temp);
      forecast.append(cell);
    });
  }

  function applyImage(card) {
    // The responsive preview's transition layer owns the visible image.
    // Select the 2:1 asset for medium rather than stretching a square one.
    const season = document.querySelector('[data-season].selected')?.dataset.season || "fall";
    const weather = document.querySelector('[data-condition].selected')?.dataset.condition || "sunny";
    const phase = document.querySelector('[data-phase].selected')?.dataset.phase || "day";
    const edition = window.SeasonalEditionPreview?.selectedEdition || "standard";
    const base = edition === "standard" ? season : "holiday_" + edition;
    const path = "assets/backgrounds/" + base + "_" + weather + "_" + phase +
      (size === "medium" ? "_wide" : "") + ".jpg";
    const layers = card.querySelectorAll(".scene-layer");
    const visibleLayer = layers[layers.length - 1];
    if (visibleLayer) {
      const target = 'url("' + path + '")';
      if (visibleLayer.style.backgroundImage !== target) {
        visibleLayer.style.backgroundImage = target;
      }
    }
    const bg = card.style.backgroundImage;
    if (!bg || bg === "none") return;
    const chosen = 'url("' + path + '")';
    if (bg !== chosen) card.style.backgroundImage = chosen;
  }

  function setSize(next) {
    size = next;
    cards.forEach(card => {
      card.classList.toggle("is-medium-preview", size === "medium");
      extendForecast(card);
      applyImage(card);
    });
    document.querySelectorAll(".size-selector button").forEach(button => {
      const selected = button.dataset.size === size;
      button.classList.toggle("is-active", selected);
      button.setAttribute("aria-pressed", String(selected));
    });
    const sizeLabel = document.querySelector(".stage-note-side");
    if (sizeLabel) sizeLabel.textContent = size === "medium" ? "2 × 1" : "1 × 1";
    const footnote = document.querySelector(".sample-disclaimer");
    if (footnote) footnote.textContent = (size === "medium" ? "Five" : "Three") +
      " illustrative hourly forecasts. The installed widget uses live weather.";
  }

  const pane = document.querySelector(".live-pane");
  if (pane) {
    const selector = document.createElement("div");
    selector.className = "size-selector";
    selector.setAttribute("role", "group");
    selector.setAttribute("aria-label", "Widget size");
    selector.innerHTML = '<button type="button" data-size="small" aria-pressed="true">Small <span>1:1 · 3 hours</span></button><button type="button" data-size="medium" aria-pressed="false">Medium <span>2:1 · 5 hours</span></button>';
    const card = document.getElementById("preview-widget");
    pane.insertBefore(selector, card);
    selector.querySelectorAll("button").forEach(button => button.addEventListener("click", () => {
      setSize(button.dataset.size);
    }));
  }

  for (const card of cards) {
    const grid = card.querySelector(".forecast-grid");
    if (grid) {
      new MutationObserver(() => {
        if (size === "medium" && grid.children.length === 3) extendForecast(card);
      }).observe(grid, {childList: true});
    }
    new MutationObserver(() => applyImage(card))
      .observe(card, {attributes:true,attributeFilter:["style"]});
    // Catch each new background layer after the original app updates weather.
    new MutationObserver(() => applyImage(card))
      .observe(card, {childList:true});
  }
  window.addEventListener("sw-edition-change", () => cards.forEach(applyImage));
  setSize("small");
})();
