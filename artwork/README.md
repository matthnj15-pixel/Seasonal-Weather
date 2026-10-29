# Photoreal Holiday Artwork | Production Branch

This branch is for **real AI-rendered scene images**. The live GitHub Pages installer continues to use the previous working assets on `main` until the new art passes review.

## Source rules

- No people, hands, crowds, or human silhouettes.
- Every file is a **full-bleed, independent landscape**. No labels, photo grids, borders, UI, logos, or typography.
- Each photo is genuinely AI-rendered, not procedural geometry or transparently layered decorations.
- Holiday subjects have believable materials, natural occlusion, integrated ground contact, reflections, shadows, depth, and environmental lighting.
- Leave readable areas for the widget. Square layout needs a central vertical forecast-safe region; wide needs clear left and bottom text areas.
- Square and wide require independently composed source frames; never upscale or crop a square frame as the published wide art.

## Required scenes

Ten editions: `christmas`, `july4`, `newyear`, `easter`, `thanksgiving`, `halloween`, `memorial`, `labor`, `birthday_a` (Oct 6), `birthday_b` (Jul 9).

Eight weather values: `sunny`, `partly`, `cloudy`, `rain`, `heavy`, `storm`, `snow`, `fog`.

Three phases: `day`, `twilight`, `night`.

Two aspect ratios: 1:1 and 2:1. Target 1024×1024 and 1536×768 JPGs; **480** finished backgrounds.

Use exact filenames:

```text
artwork/photoreal/holiday_christmas_snow_night.jpg
artwork/photoreal/holiday_christmas_snow_night_wide.jpg
artwork/photoreal/holiday_halloween_fog_twilight.jpg
artwork/photoreal/holiday_halloween_fog_twilight_wide.jpg
```

## Creative direction

- **Christmas:** full-size illuminated tree, heavy evergreen boughs, lanterns, presents, realistically lit snow.
- **July 4:** enormous fireworks, fixed ground-level sparkling fountains, river or lake reflections, no crowds.
- **Easter:** ground-level lens near flowers and a generous collection of realistically shaded decorated eggs.
- **Halloween:** elaborate moonlit graveyard, glowing carved pumpkins, stone monuments, non-anthropomorphic wisps, mist, twisted trees.
- **Thanksgiving:** substantial harvest still life, rustic autumn setting.
- **New Year:** nighttime city or lakeside fireworks in elegant gold/silver palette.
- **Memorial:** dignified memorial garden, poppies and flags; no fireworks or parties.
- **Labor:** warm lakeside picnic, late-summer decorations.
- **Oct 6 birthday:** burgundy/gold garden celebration, cake and balloons, autumn.
- **Jul 9 birthday:** brighter garden celebration, pastel balloons, cake, summer.

## Build policy

`tools/install_rendered_art.py` validates ratio/resolution and copies supplied originals without changing their image content. Use `--strict` before merging into `main` to require all 480 rendered scenes.

The previous procedural generator stays on `main` until all replacement artwork exists. **Do not publish generated contact sheets or upscale their tiny panels to satisfy filenames.** Treat any generated concept board solely as reference.

## QA

Review the 10 flagship scenes in both sizes at actual iPhone widget size and confirm forecast visibility. Check the remaining day/weather variants for correct precipitation, time-of-day, no unintended people/text, and continuous visual identity. Use the existing calendar tests unchanged.
