# Catalog freshness audit — 2026-09-28

Audit of the packaged mission catalog (`src/eo_feasibility_lint/data/missions.yaml`,
`catalog_version: "2026-08-15.1"`, catalog baseline 2026-08-15) against the
current first-party documentation of the mission operators.

- **Audited catalog version:** `2026-08-15.1` (unchanged by this audit)
- **Ruleset version:** `0.1.0` (unchanged)
- **Accessed:** 2026-09-28 for every source below
- **Allowed sources:** ESA, Copernicus (SentiWiki, Copernicus Data Space
  Ecosystem), USGS. No encyclopedia, blog, aggregator or AI-generated summary
  was used.
- **Method:** each source page was retrieved with a plain HTTP GET, reduced to
  text, and the catalog value was compared with what the page states *today*.
  Only mission-level nominal capability statements were adopted. Nothing was
  inferred.

**Result: no catalog value changed.** Every catalogued fact is confirmed by a
current first-party statement. Two provenance observations are recorded
(one `SOURCE_CHANGED`, one `AMBIGUOUS`); neither changes a value, and neither
was acted on in this audit, because a provenance change alters report output
(`source_ids`) and therefore requires a `catalog_version` bump and a
deliberate maintainer decision.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| `CURRENT` | The current first-party source states the catalogued value. No action. |
| `UPDATED` | A first-party source clearly states a different value; the catalog was changed. |
| `AMBIGUOUS` | First-party pages disagree or are unclear; both citations recorded, catalog unchanged. |
| `SOURCE_CHANGED` | The value is still confirmed, but a cited source URL moved or no longer states the fact. |
| `DEPRECATED` | The fact or source no longer applies (for example, mission ended). |

## 1. Constellation status in 2026 (context for the revisit facts)

The catalog has no explicit "operational status" field. Its nominal revisit
facts implicitly assume the operators' nominal constellation configuration.
The current official position is:

- **Sentinel-1.** Sentinel-1B ended (anomaly 23 December 2021, end of mission
  announced 3 August 2022). Sentinel-1C launched 5 December 2024, fully
  operational since early May 2025. Sentinel-1D launched 4 November 2025,
  operational from mid-April 2026. Sentinel-1A ended in June 2026 (ESA Facts and
  figures: "ended in June 2026"; SentiWiki still words it as "planned for end of
  June 2026"). The two-satellite constellation is now Sentinel-1C + Sentinel-1D.
  ESA still states a six-day revisit at the equator for the two-satellite
  constellation, so the `equator_two_satellite_nominal` 6-day value remains
  correct. SentiWiki notes the C/D configuration introduces "a one-day shift in
  the six-day revisiting pattern", which does not change the interval.
- **Sentinel-2.** Nominal constellation is Sentinel-2B + Sentinel-2C
  (Sentinel-2C replaced Sentinel-2A in operation on 21 January 2025).
  Sentinel-2A runs an *extension campaign* since March 2025, "exceptionally
  complementing" the nominal pair, prolonged until 31 December 2026. The
  nominal constellation revisit is still stated as 5 days; the extension
  campaign's improved revisit is regional and non-nominal, so it is **not**
  adopted.
- **Landsat 8 / Landsat 9.** Both operating. No USGS headline between the
  catalog baseline and 2026-09-28 reports a change of orbit, repeat cycle or
  instrument status. (Landsat 9 had a brief safehold in October 2025 and
  returned to normal operations, announced 19 November 2025 — before the
  catalog baseline, and not a capability change.)

## 2. Per-fact audit

### sentinel-2

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| sentinel-2 | constellation (implicit) | nominal two-satellite constellation | nominal pair 2B + 2C; 2A extension campaign until 2026-12-31 (non-nominal) [S2M, CDSE-S2A] | CURRENT | none |
| sentinel-2 | modalities | optical_multispectral | single MSI payload, 13 bands VNIR–SWIR [S2M] | CURRENT | none |
| sentinel-2 | bands.visible | 10 m | B2/B3/B4 at 10 m [S2M] | CURRENT | none |
| sentinel-2 | bands.nir | 10 m | B8 (~833/842 nm) at 10 m [S2M] | CURRENT | none |
| sentinel-2 | bands.red_edge | 20 m | four red-edge bands at 20 m [S2M] | CURRENT | none |
| sentinel-2 | bands.swir | 20 m | B11/B12 at 20 m [S2M] | CURRENT | none |
| sentinel-2 | bands.coastal_aerosol | 60 m | B1 (~443 nm) at 60 m [S2M] | CURRENT | none |
| sentinel-2 | bands.water_vapor | 60 m | B9 (~945 nm) at 60 m [S2M] | CURRENT | none |
| sentinel-2 | bands.cirrus | 60 m | B10 (~1375 nm) at 60 m [S2M] | CURRENT | none |
| sentinel-2 | bands.panchromatic / thermal_ir / c_band_sar | not available | 13-band MSI inventory has none of these [S2M] | CURRENT | none |
| sentinel-2 | default_multispectral_gsd_m | 10 | four 10 m bands (RGB + NIR) [S2M] | CURRENT | none |
| sentinel-2 | nominal_revisit | 5 days, equator_constellation_nominal | 5 days at the Equator, nominal constellation; 10 days single satellite [S2M] | CURRENT | none |
| sentinel-2 | swath_km | 290 | 290 km [S2M] | CURRENT | none |
| sentinel-2 | night_support.reflected_optical | false | MSI is passive, collects reflected sunlight [S2M] | CURRENT | none |
| sentinel-2 | all_weather | false | passive reflected-sunlight imager; orbit time chosen to minimise cloud cover [S2M] | CURRENT | none |

### sentinel-1-iw

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| sentinel-1-iw | constellation (implicit) | nominal two-satellite constellation | 1A ended June 2026, 1B ended 2022; two-satellite constellation is 1C + 1D [S1FF, S1M] | CURRENT | none (see §1) |
| sentinel-1-iw | modalities | sar_c_band | C-band SAR at 5.405 GHz [S1FF, S1M] | CURRENT | none |
| sentinel-1-iw | bands.c_band_sar resolution | 5 m range × 20 m azimuth | IW: 250 km swath at 5 m by 20 m (single look) [S1M, S1FF] | CURRENT | none |
| sentinel-1-iw | bands.c_band_sar provenance (`esa-sentiwiki-s1-products`) | cited for resolution and swath | products page gives product-level values only: IW SLC 2.7–3.5 × 22 m, IW GRD-HR 20 × 22 m; states no 250 km swath [S1P] | AMBIGUOUS | none; see open question Q1 |
| sentinel-1-iw | optical / thermal band families | not available | SAR-only payload (plus AIS on 1C/1D, not an imaging band) [S1FF, S1M] | CURRENT | none |
| sentinel-1-iw | nominal_revisit | 6 days, equator_two_satellite_nominal | "Six days (at the equator) from two-satellite constellation" [S1FF]; "6 day exact repeat cycle" [S1M] | CURRENT | none; see Q2 |
| sentinel-1-iw | swath_km | 250 | 250 km IW swath [S1M, S1FF] | CURRENT | none |
| sentinel-1-iw | night_support.c_band_sar | true | operates day and night [S1M] | CURRENT | none |
| sentinel-1-iw | all_weather | true | "acquire imagery regardless of the weather"; not impeded by cloud cover [S1M] | CURRENT | none (README already bounds the semantics) |

### landsat-8

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| landsat-8 | operational status (implicit) | operating | operating; no status change reported [L8, USGS-HL] | CURRENT | none |
| landsat-8 | modalities | optical_multispectral, thermal_ir | OLI + TIRS [L8] | CURRENT | none |
| landsat-8 | bands.visible | 30 m | Bands 2–4 at 30 m [L8] | CURRENT | none |
| landsat-8 | bands.coastal_aerosol | 30 m | Band 1 at 30 m [L8] | CURRENT | none |
| landsat-8 | bands.nir | 30 m | Band 5 at 30 m [L8] | CURRENT | none |
| landsat-8 | bands.swir | 30 m | Bands 6–7 at 30 m [L8] | CURRENT | none |
| landsat-8 | bands.panchromatic | 15 m | Band 8 at 15 m [L8] | CURRENT | none |
| landsat-8 | bands.cirrus | 30 m | Band 9 at 30 m [L8] | CURRENT | none |
| landsat-8 | bands.thermal_ir | 100 m | TIRS Bands 10–11 at 100 m [L8] | CURRENT | none |
| landsat-8 | bands.red_edge / water_vapor / c_band_sar | not available | 11-band OLI/TIRS inventory has none of these [L8] | CURRENT | none |
| landsat-8 | default_multispectral_gsd_m | 30 | 30 m multispectral, 15 m pan [L8] | CURRENT | none |
| landsat-8 | nominal_revisit | 16 days, nominal_repeat_cycle | 16-day repeat cycle [L8, FAQ] | CURRENT | none |
| landsat-8 | swath_km | 185 | 185 km swath [L8, FAQ] | CURRENT | none |
| landsat-8 | night_support (reflected bands) | false | nominal plan images day-lit scenes (sun ≥ 5°) on descending passes [LTAP, FAQ] | CURRENT | none; see Q3 |
| landsat-8 | night_support.thermal_ir | occasional | ascending nighttime scenes only by special request [LTAP] | CURRENT | none |
| landsat-8 | all_weather | false | passive OLI/TIRS; descending overpass time chosen for less haze and cloud buildup [L8, FAQ] | CURRENT | none |

### landsat-9

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| landsat-9 | operational status (implicit) | operating | operating; October 2025 safehold resolved [L9, USGS-HL] | CURRENT | none |
| landsat-9 | modalities | optical_multispectral, thermal_ir | OLI + TIRS [L9] | CURRENT | none |
| landsat-9 | bands.visible | 30 m | Bands 2–4 at 30 m [L9] | CURRENT | none |
| landsat-9 | bands.coastal_aerosol | 30 m | Band 1 at 30 m [L9] | CURRENT | none |
| landsat-9 | bands.nir | 30 m | Band 5 at 30 m [L9] | CURRENT | none |
| landsat-9 | bands.swir | 30 m | Bands 6–7 at 30 m [L9] | CURRENT | none |
| landsat-9 | bands.panchromatic | 15 m | Band 8 at 15 m [L9] | CURRENT | none |
| landsat-9 | bands.cirrus | 30 m | Band 9 at 30 m [L9] | CURRENT | none |
| landsat-9 | bands.thermal_ir | 100 m | TIRS Bands 10–11 at 100 m [L9] | CURRENT | none |
| landsat-9 | bands.red_edge / water_vapor / c_band_sar | not available | 11-band OLI/TIRS inventory has none of these [L9] | CURRENT | none |
| landsat-9 | default_multispectral_gsd_m | 30 | 30 m GSD for all bands except 15 m pan [L9] | CURRENT | none |
| landsat-9 | nominal_revisit | 16 days, nominal_repeat_cycle | 16-day repeat cycle [L9, FAQ] | CURRENT | none |
| landsat-9 | swath_km (value) | 185 | 185 km per satellite [FAQ]; ~185 × 180 km WRS-2 scenes [LTAP] | CURRENT | none |
| landsat-9 | swath_km provenance (`usgs-landsat-9` only) | cited as sole source | current Landsat 9 page states no swath width | SOURCE_CHANGED | none now; see Q4 |
| landsat-9 | night_support (reflected bands) | false | day-lit nominal imaging [LTAP, FAQ] | CURRENT | none; see Q3 |
| landsat-9 | night_support.thermal_ir | occasional | ascending nighttime scenes only by special request [LTAP] | CURRENT | none |
| landsat-9 | all_weather | false | passive OLI/TIRS [L9, FAQ] | CURRENT | none |

### landsat-8-9 (combined cadence)

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| landsat-8-9 | constellation (implicit) | Landsat 8 + Landsat 9 both operating | both operating [USGS-HL, FAQ] | CURRENT | none |
| landsat-8-9 | nominal_revisit | 8 days, nominal_combined_offset | "they can capture images of the same area every eight days" [FAQ]; "8-day offset" [L8, L9] | CURRENT | none |
| landsat-8-9 | swath_km | 185 | 185 km per satellite [FAQ, L8] | CURRENT | none |
| landsat-8-9 | modalities and band table | identical to landsat-8 / landsat-9 | Landsat 9 OLI "is a copy of that on Landsat 8"; same band list [L8, L9] | CURRENT | none |
| landsat-8-9 | default_multispectral_gsd_m | 30 | 30 m [L8, L9] | CURRENT | none |
| landsat-8-9 | night_support | reflected false, thermal occasional | as landsat-8 / landsat-9 [LTAP] | CURRENT | none |
| landsat-8-9 | all_weather | false | as landsat-8 / landsat-9 | CURRENT | none |

### Source URL health (all catalog sources)

| Mission | Field | Current catalog | First-party current value | Status | Action |
| --- | --- | --- | --- | --- | --- |
| (all) | `esa-sentiwiki-s2-mission` URL | https://sentiwiki.copernicus.eu/web/s2-mission | HTTP 200, no redirect | CURRENT | none |
| (all) | `esa-s1-facts-and-figures` URL | https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Facts_and_figures | HTTP 200, no redirect | CURRENT | none |
| (all) | `esa-sentiwiki-s1-mission` URL | https://sentiwiki.copernicus.eu/web/s1-mission | HTTP 200, no redirect | CURRENT | none |
| (all) | `esa-sentiwiki-s1-products` URL | https://sentiwiki.copernicus.eu/web/s1-products | HTTP 200, no redirect | CURRENT | none |
| (all) | `usgs-landsat-8` URL | https://www.usgs.gov/landsat-missions/landsat-8 | HTTP 200 on GET, no redirect (HEAD returns 403) | CURRENT | none |
| (all) | `usgs-landsat-9` URL | https://www.usgs.gov/landsat-missions/landsat-9 | HTTP 200 on GET, no redirect (HEAD returns 403) | CURRENT | none |
| (all) | `usgs-landsat-acquisition-schedules` URL | https://www.usgs.gov/faqs/what-are-acquisition-schedules-landsat-satellites | HTTP 200 on GET, no redirect (HEAD returns 403) | CURRENT | none |
| (all) | `usgs-landsat-acquisition-plan` URL | https://www.usgs.gov/data/landsat-89-long-term-acquisition-plan-earths-continental-landmasses-and-near-shore-coastal | HTTP 200 on GET, no redirect (HEAD returns 403); page title carries a "Version 1.0" suffix that the catalog title omits | CURRENT | none |

### Status counts

| Status | Count |
| --- | --- |
| CURRENT | 70 |
| UPDATED | 0 |
| AMBIGUOUS | 1 |
| SOURCE_CHANGED | 1 |
| DEPRECATED | 0 |
| **Total rows** | **72** |

## 3. Source archive

All accessed 2026-09-28. Quotes are verbatim and 25 words or fewer.

| Key | Catalog id | Publisher | Title | URL | Supported fact |
| --- | --- | --- | --- | --- | --- |
| S2M | `esa-sentiwiki-s2-mission` | ESA / Copernicus (SentiWiki) | S2 Mission | https://sentiwiki.copernicus.eu/web/s2-mission | "designed to give a high revisit frequency of 5 days at the Equator." / "13 spectral bands: four bands at 10 m, six bands at 20 m and three bands at 60 m spatial resolution. The orbital swath width is 290 km." / "The MSI works passively, by collecting sunlight reflected from the Earth." / "Sentinel-2C has replaced Sentinel-2A in operation on January 21st, 2025" / "the nominal constellation operations configuration revisit is 5 days." |
| S1FF | `esa-s1-facts-and-figures` | ESA | Facts and figures (Sentinel-1) | https://www.esa.int/Applications/Observing_the_Earth/Copernicus/Sentinel-1/Facts_and_figures | "Revisit time: Six days (at the equator) from two-satellite constellation" / "Interferometric wide-swath mode at 250 km and 5×20 m spatial resolution" / "Sentinel-1A on 3 April 2014 (ended in June 2026)" / 1B ended August 2022; 1C launched 5 December 2024; 1D launched 4 November 2025. |
| S1M | `esa-sentiwiki-s1-mission` | ESA / Copernicus (SentiWiki) | S1 Mission | https://sentiwiki.copernicus.eu/web/s1-mission | "operating day and night performing C-band synthetic aperture radar imaging, enabling them to acquire imagery regardless of the weather." / "It acquires data with a 250 km swath at 5 m by 20 m spatial resolution (single look)." / "The two-satellite constellation offers a 6 day exact repeat cycle." / "the final two-satellite constellation will consist of Sentinel-1C and Sentinel-1D." |
| S1P | `esa-sentiwiki-s1-products` | ESA / Copernicus (SentiWiki) | S1 Products | https://sentiwiki.copernicus.eu/web/s1-products | Level-1 resolution table: IW SLC resolution 2.7×22 to 3.5×22 m (rng × azi); IW GRD High Resolution 20×22 m at 10×10 m pixel spacing. No mission-level swath figure. |
| L8 | `usgs-landsat-8` | USGS | Landsat 8 | https://www.usgs.gov/landsat-missions/landsat-8 | "Landsat 8 images have 15-meter panchromatic and 30-meter multi-spectral spatial resolutions along a 185 km (115 mi) swath." / "Has a 16-day repeat cycle … 8-day offset with Landsat 9" / TIRS Bands 10–11 at 100 m. |
| L9 | `usgs-landsat-9` | USGS | Landsat 9 | https://www.usgs.gov/landsat-missions/landsat-9 | "maximum ground sampling distance (GSD) … of 30-meters(m) (98 feet) for all bands except the panchromatic band, which has a 15-meter (49 feet) GSD." / "Has a 16-day repeat cycle … 8-day offset with Landsat 8" / TIRS "100 m (328 ft) for both bands". |
| FAQ | `usgs-landsat-acquisition-schedules` | USGS | What are the acquisition schedules for the Landsat satellites? | https://www.usgs.gov/faqs/what-are-acquisition-schedules-landsat-satellites | "Each satellite captures images across a 185-kilometer, or 115-mile, swath." / "passes over the same location once every 16 days. Because their orbits are offset, they can capture images of the same area every eight days." |
| LTAP | `usgs-landsat-acquisition-plan` | USGS | The Landsat 8/9 Long Term Acquisition Plan for Earth's continental landmasses and near-shore coastal zones, Version 1.0 | https://www.usgs.gov/data/landsat-89-long-term-acquisition-plan-earths-continental-landmasses-and-near-shore-coastal | "Ascending nighttime, open ocean, and Landsat Extended Acquisitions of the Poles (LEAP) scenes are only acquired by special request" / "A scene is considered day-lit when the solar elevation at scene center is at least 5 degrees above the horizon." |
| CDSE-S2A | (context only, not in catalog) | Copernicus Data Space Ecosystem | Sentinel-2A Extension Campaign Prolonged Until the End of 2026 (2026-05-15) | https://dataspace.copernicus.eu/news/2026-5-15-sentinel-2a-extension-campaign-prolonged-until-end-2026 | "Sentinel-2A will continue to operate under the tailored operational scenario introduced in 2025 until 31 December 2026" |
| USGS-HL | (context only, not in catalog) | USGS | Landsat Mission Headlines | https://www.usgs.gov/landsat-missions/landsat-mission-headlines | 2026 headlines report no Landsat 8 or 9 orbit, repeat-cycle or instrument change; "Landsat 9 Returns to Normal Operations Following Brief Safehold" (2025-11-19). |

## 4. Open questions for the maintainer

- **Q1 (AMBIGUOUS, provenance).** `esa-sentiwiki-s1-products` is cited for
  `swath_km` and `bands.c_band_sar` of `sentinel-1-iw`, but the page currently
  states only product-level figures (IW SLC 2.7–3.5 × 22 m; IW GRD-HR 20 × 22 m)
  and no swath width. The mission-level nominal 5 × 20 m and 250 km are stated
  by the co-cited `esa-sentiwiki-s1-mission` and by `esa-s1-facts-and-figures`,
  so the catalog value is kept (mission-level nominal capability is what the
  catalog models). Consider, in a future catalog revision, citing the Facts and
  figures page for these two keys and/or documenting the SLC/GRD distinction.
- **Q2 (note).** SentiWiki also mentions a *potential* ascending/descending
  revisit of "3 days at the equator". This is a different quantity (both
  pass directions, observation-scenario dependent) from the 6-day repeat that
  ESA publishes as the constellation "Revisit time". The catalog keeps 6 days,
  which is the conservative operator-stated nominal value.
- **Q3 (note).** The LTAP says ascending (nighttime) scenes can be acquired by
  special request with the 5° sun-elevation constraint disabled. It does not
  distinguish OLI from TIRS. The catalog models reflected-optical night support
  as `false` and thermal as `occasional`; no current source contradicts this.
- **Q4 (SOURCE_CHANGED, provenance).** `landsat-9.capability_sources.swath_km`
  cites only `usgs-landsat-9`, whose current page states no swath width. The
  value (185 km) is confirmed by `usgs-landsat-acquisition-schedules`. Whether
  the Landsat 9 page stated it at the catalog baseline could not be verified.
  Recommended fix for a future catalog revision: add
  `usgs-landsat-acquisition-schedules` to that key (this changes the
  `source_ids` of `EFL701` findings for `landsat-9`, so it needs a
  `catalog_version` bump).
- **Next review trigger.** The Sentinel-2A extension campaign is scheduled to
  end on 2026-12-31. It never changed the nominal value, but the S2 page text
  will change; re-audit after that date.
