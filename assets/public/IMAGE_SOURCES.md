# A2 MissionLab — image source and provenance ledger

Public photography in **Through Orion’s Windows** is loaded from NASA’s Images asset service using the NASA asset IDs below. The repository does not bundle the remote NASA flight photography used by the viewer. If a network image is unavailable, `assets/public/fallback-mission.svg` appears only as an offline/network-failure fallback and is never represented as flight photography.

**Evidence rule:** a photograph is labeled as an exact event image only when NASA metadata/reporting supports that connection. MissionLab-derived geometry is kept separate from image provenance; same-phase/context images are explicitly identified as such.

| # | NASA asset | Moment | Provenance | Context source |
|---:|---|---|---|---|
| 01 | `art002e023506` | Earth begins to fall away. | **MISSION-PHASE CREW PHOTOGRAPHY** | https://www.nasa.gov/gallery/journey-to-the-moon/ |
| 02 | `art002e023710` | Home becomes a thin illuminated edge. | **EXACT MISSION IMAGE · NASA IDENTIFIED** | https://www.nasa.gov/gallery/journey-to-the-moon/ |
| 03 | `art002e014225` | Earth becomes a delicate crescent. | **EXACT MISSION IMAGE · NASA GALLERY** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 04 | `art002e009582` | The Moon stops being a dot and becomes terrain. | **EXACT MISSION IMAGE · FLYBY PERIOD** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 05 | `art002e009294` | The observation window had to be prepared before the Moon arrived. | **EXACT MISSION IMAGE · NASA IDENTIFIED** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 06 | `art002e009293` | The crew turns a fleeting view into science data. | **EXACT MISSION IMAGE · CREW OBSERVATION** | https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/ |
| 07 | `art002e012278` | The Moon rises into Orion’s window. | **EXACT MISSION IMAGE · WINDOW VIEW** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 08 | `art002e012273` | Orientale’s rings become a live geology target. | **EXACT MISSION IMAGE · TARGET IDENTIFIED BY NASA** | https://www.nasa.gov/gallery/lunar-flyby/page/2/ |
| 09 | `art002e012702` | Two craters reveal different impact histories in one frame. | **EXACT MISSION IMAGE · FEATURES IDENTIFIED BY NASA** | https://www.nasa.gov/gallery/lunar-flyby/page/2/ |
| 10 | `art002e010208` | The day–night boundary turns subtle relief into dramatic structure. | **EXACT MISSION IMAGE · LIVE OBSERVATION CONTEXT** | https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/ |
| 11 | `art002e009283` | The far side becomes a heavily cratered archive. | **EXACT MISSION IMAGE · REGION IDENTIFIED BY NASA** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 12 | `art002e009282` | Long shadows turn Vavilov into a relief map. | **EXACT MISSION IMAGE · FEATURE IDENTIFIED BY NASA** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 13 | `art002e012093` | Hertzsprung’s concentric rings come into view. | **EXACT MISSION IMAGE · TARGET IDENTIFIED BY NASA** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 14 | `art002e012279` | Earth approaches the lunar horizon. | **NEAR-EVENT IMAGE · NASA TIME CONTEXT** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 15 | `art002e009288` | Earth disappears behind the Moon. | **EXACT EVENT IMAGE · NASA TIMESTAMP** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 16 | `jsc2026e020490` | The view through the window has a team in Houston behind it. | **GROUND CONTEXT · EXACT NASA IMAGE** | https://images.nasa.gov/details/jsc2026e020490 |
| 17 | `art002e009289` | Behind the Moon, silence is expected. | **SAME-PHASE IMAGE · NASA REPORTED EVENT** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 18 | `art002e009299` | Closest approach happens inside a moving landscape. | **MISSIONLAB DERIVED EVENT · SAME-PHASE IMAGE** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 19 | `art002e009301` | The Moon covers the Sun from deep space. | **MISSION IMAGE + DERIVED INTERVAL** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 20 | `art002e009298` | Darkness turns the lunar night side into an observation field. | **MISSION IMAGE · IMPACT-FLASH CONTEXT** | https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/ |
| 21 | `art002e009573` | An eclipse becomes a deep-space composition. | **EXACT MISSION IMAGE · ECLIPSE PERIOD** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 22 | `art002e021278` | Earth returns over the lunar horizon. | **EXACT EVENT IMAGE · NASA TIMESTAMP** | https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/ |
| 23 | `art002e016299` | The same geometry looks different from outside Orion. | **EXACT MISSION IMAGE · EXTERNAL CAMERA** | https://www.nasa.gov/gallery/lunar-flyby/page/3/ |
| 24 | `art002e016354` | The Moon starts shrinking behind Orion. | **EXACT MISSION IMAGE · RETURN COAST** | https://www.nasa.gov/gallery/lunar-flyby/ |
| 25 | `art002e012588` | The journey home opens a window on the galaxy. | **EXACT MISSION IMAGE · RETURN PHASE** | https://www.nasa.gov/general/artemis-ii-mission-milestones-an-image-and-video-recap/ |

## Primary NASA collections and science context

- Artemis II lunar flyby gallery: https://www.nasa.gov/gallery/lunar-flyby/
- Artemis II journey-to-the-Moon gallery: https://www.nasa.gov/gallery/journey-to-the-moon/
- Official flyby photo release: https://www.nasa.gov/news-release/nasas-artemis-ii-crew-beams-official-moon-flyby-photos-to-earth/
- Flight Day 6 lunar-flyby updates: https://www.nasa.gov/blogs/missions/2026/04/06/artemis-ii-flight-day-6-lunar-flyby-updates/
- Artemis II preliminary lunar science report: https://science.nasa.gov/feature/artemis-ii-preliminary-lunar-science-report/
- Artemis II image/video mission recap: https://www.nasa.gov/general/artemis-ii-mission-milestones-an-image-and-video-recap/
- NASA Images detail page for the Artemis science-console image: https://images.nasa.gov/details/jsc2026e020490

## Gallery behavior

- 25 moments are available through visible previous/next controls placed directly on the image, the lower timeline controls, the scrubber, thumbnails, and left/right keyboard navigation while the gallery is in view.
- The decorative interior cross-window bars from the previous public build were removed. The subtle outer Orion-window framing remains.
- Each moment exposes mission time/phase context, viewing geometry, evidence type, provenance, and why the observation mattered.
- Remote NASA image delivery is intentionally kept separate from the repository-local MissionLab diagrams and fallback art.

## Phase H celestial rendering assets

The following repository-local images are used only to improve the visual
fidelity of schematic MissionLab canvas scenes. They are not asserted to be
timestamp-specific Artemis II observations, exact spacecraft camera geometry,
private telemetry, or exact illumination/orientation states.

### Earth — NASA/JPL PIA18033

- Local asset: `assets/public/celestial/earth_pia18033.jpg`
- NASA identifier: PIA18033
- Source page: https://science.nasa.gov/image-detail/amf-pia18033/
- Direct NASA asset: https://images-assets.nasa.gov/image/PIA18033/PIA18033~large.jpg
- Producer/credit: NASA / JPL
- Source imagery: VIIRS aboard Suomi NPP
- MissionLab use: visual Earth disk material inside educational canvas scenes

### Moon — NASA SVS Moon Mosaic 5001

- Local asset: `assets/public/celestial/moon_lro_mosaic.jpg`
- NASA SVS identifier: 5001
- Source page: https://svs.gsfc.nasa.gov/5001
- Direct NASA asset: https://svs.gsfc.nasa.gov/vis/a000000/a005000/a005001/moon_mosaic_print.jpg
- Credit: NASA Scientific Visualization Studio
- Source imagery: photomosaic assembled from 1,231 LRO Narrow Angle Camera images
- MissionLab use: visual lunar disk material inside educational canvas scenes

### Rendering boundary

MissionLab clips these source images into canvas-rendered planetary disks and
adds visualization-only limb shading / atmospheric glow for scene readability.
The underlying mission trajectory, event timing, closest-approach values,
state-product boundaries, and evidence classifications are not changed by
these visual assets.
