# Cruel World

**A playable pixel-art dark-fantasy action alpha:** three heroes, three side-scrolling realms, and three bosses in a complete keyboard-driven campaign.

![Cruel World title screen](docs/media/title.png)

**[Play the current browser alpha](https://jupiternull.github.io/cruel-world/)** — desktop keyboard required. Includes the castle refuge, progression, provisions, aftermath, and expanded regions.

> **Alpha status:** Combat, balance, performance, and presentation are still evolving. The repository and GitHub Pages build include camp, expedition gates, expanded regions, persistent Blacksmith fittings, provisions, aftermath, and expedition records. A restricted itch.io playtest page and character creation remain deferred.

## Current source build features

- Knight, Ranger, and Wizard with distinct attacks, abilities, and defensive movement.
- A roamable 2200 px castle refuge with distinct service buildings and a central gatehouse with seven useful camp services, safe attack practice, and three progression-gated expeditions.
- Three expanded authored realms (3840 / 4032 / 4224 px), each with three subareas, signature environment mechanics, optional discoveries, breakable props, ambient life, checkpoints, finite waves, and telegraphed bosses.
- Directional armor, ranged targeting, hit-once projectiles, pickups, scoring, and checkpoint retries.
- Pause and focus-loss protection, settings, realm music, ambience, and combat sound effects.
- Desktop high scores and settings; a staged keyboard-only HTML5 build.

## Gameplay and screenshots

![Continuous Ranger movement and combat preview](docs/media/gameplay.gif)

Captured from sequential game-rendered frames at 60 simulation ticks per second, sampled for a 640×480 GIF. The preview runs forward then reverses the same sequence to loop smoothly; reverse playback is an editing effect.

| Class selection | Verdant Ruins |
| --- | --- |
| ![Class selection](docs/media/class-selection.png) | ![Verdant Ruins combat](docs/media/verdant-ruins.png) |
| Sunken Keep | Moon Graveyard |
| ![Sunken Keep combat](docs/media/sunken-keep.png) | ![Moon Graveyard combat](docs/media/moon-graveyard.png) |

![Earlier campaign victory screen](docs/media/victory.png)

The earlier victory menu is shown above for reference; final victory now returns to camp with a completion acknowledgement. See `artifacts/camp-contact-sheet.png` after running the camp capture.

The media above predates the regional expansion. Updated gameplay-scale region captures are generated under `artifacts/regions/` by `capture_regions.py`. The expansion combines original deterministic Cruel World scenery with curated, transformed imported subsets.

## Run locally

Python 3.10+ and Pygame 2.6.1+; interactive play requires a graphical desktop.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The public source repository does not redistribute the Hero Knight source pack or its generated runtime derivatives. For a complete local source checkout, download Hero Knight from the creator's page listed under [Assets and licenses](#assets-and-licenses), place the supplied `Hero Knight` directory at `assets/heroes/hero_knight/Hero Knight/`, then run `python build_presentation.py` before launching. Published playtest builds include the required runtime character data as part of the packaged game.

Choose **Begin campaign**, select a hero, and press Enter to enter camp. Follow the path right to the central numbered **Expedition Gates**, press E to inspect destination/enemies/boss/readiness, then E or Enter again to depart. Gate 1 starts unlocked; each regional victory unlocks the next gate. Clear two finite waves per region (five then six enemies, at most four alive), defeat the boss, and enter the glowing exit to return to camp at full health. Score resets on each departure; the final return acknowledges campaign completion. Cleared gates remain available for replay.

## Browser build

Live browser alpha: **https://jupiternull.github.io/cruel-world/**

The commands below rebuild the currently deployed camp-and-progression browser package.

Install FFmpeg with libvorbis support, then:

```bash
python -m pip install -r requirements-web.txt
python build_web.py
```

The build produces `dist/cruel-world-closed-alpha.zip`, staging runtime files and licenses and converting only staged WAV copies to OGG. Source assets remain intact. See [closed-alpha playtest and hosting instructions](PLAYTEST.md) for uploading the prepared HTML5 archive to a restricted itch.io project with an 800×600 embed, Click to Play, and fullscreen enabled.

Click the launch screen and then the game to focus it. Keyboard required; mobile/touch play is unsupported. First launch needs internet access for the pygbag runtime CDN. Browser audio requires interaction and can vary with browser policy. Browser scores/settings/progress are session-only and disappear on reload; campaign resuming is not implemented. Quit ends the game; reload to restart.

## Controls

| Key | Action |
| --- | --- |
| A/D or Left/Right | Move and face attacks |
| Space | Jump; release before another jump |
| W/Up, S/Down | Attach to and climb ladders; W also jumps from ground |
| A/D or Space while climbing | Detach sideways or jump away |
| S/Down + Space | Drop through raised platforms |
| F | Primary attack |
| E | Camp interaction; nearest unclaimed regional object within 70 px consumes E, otherwise class secondary |
| R in camp | Test class secondary ability |
| Shift or Q | Dash/evade/blink with brief invulnerability |
| Escape or P | Pause/resume; Escape closes camp dialogue first |
| Up/Down or W/S; Enter/Space | Navigate and select menu items |
| Left/Right | Select class; adjust selected setting |
| Escape in class/settings/death | Return to preceding menu/title |
| R after death | Restart campaign with current class |

Pause offers resume, settings, restart with class selection, and title. **Retry checkpoint** restores health at the reached flag, resets the current battle, and deducts 250 points (minimum zero). Restart returns to camp with the selected hero and zero run score. Losing focus pauses play; menus and pause freeze simulation, projectiles, cooldowns, and progression.

## Current classes

| Class | Health / speed | Primary (F) | Secondary (E) |
| --- | --- | --- | --- |
| Knight | 150 HP / 4 px per tick | Buffered three-strike combo: 22/30/42 damage | Shield rush: 35 damage; 3 s cooldown |
| Ranger | 100 HP / 6 px per tick | Bow arrow: 18 damage | Three piercing arrows: 24 damage each; 3.5 s cooldown |
| Wizard | 85 HP / 4 px per tick | Fireball: 26 damage | Piercing arcane wave: 50 damage, bypasses armor; 5 s cooldown |

Primary attacks release after a nine-tick windup. Knight commits to melee; Ranger and Wizard can move at half speed and jump while firing, or cancel an unreleased shot into defensive mobility. Ranged primaries aim toward the nearest threat within 560 px ahead and 280 px vertically, otherwise travel horizontally. Each damage source hits each target once. The HUD shows health, score, wave, and ability readiness. Knight/Ranger defensive movement lasts 14 ticks at 12 px/tick with a 1.5 s cooldown; Wizard blink uses 18 px/tick and a 2.5 s cooldown.

## Current realms

| Realm | Traversal and enemies | Boss / counterplay |
| --- | --- | --- |
| Verdant Ruins (3840 px) | Ruined approach → flooded grove → overgrown sanctuary; shallow pools, breakable vines, abandoned cache; goblins and flying eyes | Spore Sovereign: leave marked bursts and avoid alternating spore volleys |
| Sunken Keep (4032 px) | Collapsed halls → prison/cistern → sealed armory; lever opens traversal bars, pots/cupboard, prisoner ledger, harmless haunted statue; mushrooms and shield skeletons | Iron Marauder: armored front, sweep, lunge, shockwave; punish rear, windup, or recovery |
| Moon Graveyard (4224 px) | Outer cemetery → mausoleum row → moonlit crypt; optional three grave lanterns, urns, crypt record, bell monument; goblins, mushrooms, shield skeletons | Moon Eater: falling moon columns and diagonal shots; reposition and aim or jump into melee range |

Orange markers and translucent red areas warn of attacks. Frontal armor reduces damage to one third outside enemy windup/recovery; rear attacks and arcane waves bypass it. Gates prevent skipping battles. Raised platforms are one-way. Hazards deal 16 damage; wave clears heal 15 HP, boss clears 30 HP, returns to camp restore full HP, and health pickups 30 HP.

Regional interactions are fast and optional except the Keep lever, which raises the cistern gate over 48 simulation ticks with a visible opening animation and door sound. The Knight ground route reaches every required object; ladders and perches provide alternate routes. Shallow forest water scales horizontal movement to 75% (integer movement gives Ranger 4 px/tick, Knight/Wizard 3), only while grounded; jump velocity is unchanged. Vine barriers accept ordinary hero melee, arrows, fireballs, and secondary damage sources. Environmental breakables give 25 score / 3 HP once. Cache/ledger/record discoveries give 120 score / 12 HP; landmarks give 60 score; all three grave lanterns give 180 score / 18 HP once and illuminate the bell monument threshold. Descriptions are deliberately ambiguous atmosphere, not canonical history.

Regional claims, lit lanterns, and destroyed props persist during checkpoint retries to prevent reward farming. The Keep gate resets closed when retrying before it, with its lever available again; checkpoints beyond it restore an open gate. A new expedition resets all regional features. Ambient animation uses deterministic tick formulas and never touches global random state. Pause freezes the full feature simulation. Fog/spray stay translucent and close to the ground; scenery remains behind combat actors and collision surfaces.

`build_region_assets.py` regenerates nine original 600×220 scene panels (rendered 2× nearest-neighbor). Existing derivative strips are retained and their manifest refreshed without external files. To regenerate imported subsets, provide `--sources /path/to/external/extractions`; this is development-only and the external packs are never needed at runtime or by `build_web.py`. Derivative recipes/crops, dimensions, frame counts, palettes, and SHA-256 records are in `assets/regions/derivatives.json`. Original scenery includes arches, sanctuary statue, tents/camp remnants, trees/reeds, cells, cistern, chains/chandeliers, throne-cell, graves, crypts, fences, memorial statues, coffins/bones, lanterns/candles, and bell monument. Anokolisa's existing ruins and underused Moon Graveyard wrought fence tiles are composed with it.

Regional verification/captures:

```bash
python build_region_assets.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m unittest discover -s tests
python verify_campaign.py --output artifacts/regions-campaign
python capture_regions.py
python build_web.py
```

`tests/test_regions.py` verifies licenses byte-for-byte by retained term hashes, derivatives, original art determinism, class attacks against vines, one-time rewards, water, gate/reset/collision, statue safety, lanterns, E priority, pause, browser inclusion, and rendering/bounds for every hero and subarea. The campaign bot handles only required vines/lever and ignores optional discoveries/lanterns. `capture_regions.py` produces nine eight-view contact sheets at full 800×600 gameplay scale, plus 72 direct captures covering all subareas, discoveries, mechanisms before/after, landmarks, and boss arenas. Headless verification cannot establish real-browser input/audio quality or subjective human combat balance. The original panels use restrained silhouettes and worn masonry rather than character-grade animation; live browser testing remains necessary.

## Feedback

Use GitHub Issues with the **Bug report** or **Playtest feedback** template. Include OS/browser, class, realm/wave, reproduction steps, and screenshots or video where useful. Feedback on attack commitment, dodge timing, readability, difficulty spikes, navigation, audio, and browser performance is especially useful. See [PLAYTEST.md](PLAYTEST.md) for browser caveats.

## Roadmap — planned

These are development directions, not shipped features or dated promises.

- **Next alpha:** restricted itch.io deployment, broader desktop/browser playtesting, balance and readability passes, performance and input-feel fixes.
- **Character identity:** controlled character creation, expanded class selection, and subclasses with distinct roles and tradeoffs.
- **Base camp expansion:** deeper functional services, crafting, and camp development beyond the current courtyard.
- **Expeditions and progression:** prepare at camp, undertake expeditions, master bosses, collect materials, and develop equipment and camp services.
- **World and art:** custom original pixel art, richer NPC and faction relationships, and deeper lore supplied later by the creator. Current names and encounters do not establish future lore canon.
- **Optional exploration:** evaluate procedural expeditions assembled from authored chunks while retaining intentional encounter design and readable traversal.

## Long-term vision

Cruel World is intended to grow into a side-scrolling pixel-art dark-fantasy action RPG. Design influences are principles: deliberate Soulslike combat and environmental storytelling; Monster Hunter-style preparation, boss mastery, and material progression; and MMO-like class identity, factions, and NPC world depth. These influences describe the intended experience; multiplayer is not a current feature or a commitment.

The planned rhythm is a living camp, purposeful preparation, dangerous expeditions, and lasting progression. Story and lore will be developed later rather than filled in with invented canon here.

## Development and verification

Simulation runs at a fixed 60 Hz, independently of rendering. `main.py` handles events and menus; `campaign.py` owns authored traversal/progression; `entities/hero.py` and `entities/monster.py` implement combat. `camp.py` owns the separate courtyard world, original deterministic art, interactions, services, and dummy. `camera.py`, `projectile.py`, `scenery.py`, `ui.py`, `audio.py`, and `persistence.py` support rendering and services.

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py assets.py audio.py camera.py campaign.py projectile.py scenery.py config.py game_state.py persistence.py ui.py level.py entities tests build_web.py build_presentation.py capture_presentation.py capture_gameplay.py verify_campaign.py
git diff --check
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy CRUELWORLD_SAVE_PATH=/tmp/cruel-smoke.json python main.py --class wizard --environment 3 --frames 120 --screenshot /tmp/cruel-smoke.png
python verify_campaign.py --ticks 60000 --output /tmp/cruel-campaign-verification
```

`--class` starts directly in an expedition; add `--camp` for camp or `--storehouse` for the interior; `--environment 1|2|3` selects a debug realm; `--frames` bounds rendering; `--screenshot` saves the final frame. Without `--class`, play starts at the title. The campaign verifier uses ordinary attacks and checkpoint retries, captures all nine class/realm bosses, and fails unless every class wins with at most five retries. Bots supplement desktop/browser playtesting.

`capture_camp.py` saves exterior depth views, indoor entrance/counter/ledger/rack/exit, three dialogue states, authored art, and the gameplay-scale contact sheet to `artifacts/`. `capture_presentation.py` captures menus and class/realm views into ignored development output. To regenerate the continuous gameplay GIF, install Pillow (`python -m pip install Pillow`) and run `python capture_gameplay.py`; frames stay in memory and saves use a temporary directory. `build_presentation.py` deterministically rebuilds curated Knight/Ranger derivatives and the logo without changing source packs.

Desktop saves use atomic schema-versioned storage at `$XDG_DATA_HOME/cruelworld/save.json` or `~/.local/share/cruelworld/save.json`; override with `CRUELWORLD_SAVE_PATH` for isolated testing. Saves retain high score, settings, selected class, furthest realm, and cleared regions, class fittings, provisions, and completed expedition records (schema 4), not a resumable run. Version-2 saves infer prior victories from the furthest visited region so previously reached gates remain available. Legacy scores/settings and `huntress` IDs migrate safely. Corrupt values default safely; write errors appear in the UI. Missing audio degrades to fallbacks; required invalid sprites cause a clear startup error.


## Camp services and original assets

The SUPPLIES storehouse is the first enterable building: approach its recessed door and press E/Enter. A short fade leads into a 1120px authored hall; the courtyard exit returns you to the same threshold and exterior camera. The Quartermaster works inside at the counter, offering a single expedition provision. The expedition ledger lists all three routes, lock/clear state, enemies, and bosses without departing. The preparation rack reports class primary/secondary, defensive movement, damage, maximum health, speed, and controls. The ledger and preparation rack only inspect readiness; the counter selects a provision. Other service buildings remain exterior services. The Blacksmith forges and equips one bounded class fitting. The Scout/Cartographer shows route availability; each physical gate supplies exact enemies and boss. The Healer restores full health or reports that you are already well. The Arcanist explains the selected secondary ability and recovery. The Trainer gives class controls and tracks hits on the straw dummy at the right wall. The Chronicler opens persistent regional discovery, material, hero completion, class best score, and provision records. NPCs cannot be damaged; practice grants no score. E/Enter closes ordinary dialogue; Escape closes fitting, provision, journal, or dialogue panels before pause. Dialogue freezes movement and attack simulation.

`camp_interior.py` owns the separate supply hall, its inspection panels, deterministic shelving, timber roof, masonry, reserve cage, weapon bundles, maps, barrels, herbs, ropes, lanterns, workers, and foreground lintel. Normal movement/collision stays active in both worlds; interiors have no combat practice. Temporary attacks and particles clear at doorway transitions while the hero and campaign state persist. `camp.py` creates the original 1100×300 refuge and 24×36 NPC sprites at runtime, scaled exactly 2× with nearest-neighbor sampling. Source generation is deterministic and does not edit imported art. `python build_camp_audio.py` rebuilds original mono 22050 Hz, 16-second WAV loops in `assets/audio/camp/`: a plucked harmonic instrument/drone score and restrained filtered village/fire noise with distant forge taps. A third loop, `interior.wav`, adds original restrained lantern hiss and periodic wood resonances. The storehouse uses quieter camp music and replaces courtyard ambience with this room tone; exiting restores the outdoor mix. These are original Cruel World assets created for this implementation, without third-party samples. Music and ambience use independent reserved mixer channels and obey Sound/Volume settings. Pause freezes both loops and fade clocks; resume restores their playback positions.

Verification and capture additions:

```bash
.venv/bin/python build_camp_audio.py
.venv/bin/python capture_camp.py
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy CRUELWORLD_SAVE_PATH=/tmp/cruel-camp-smoke.json .venv/bin/python main.py --class warrior --camp --frames 120 --screenshot artifacts/camp-smoke.png
```

Use `--class warrior` for the Knight (the class ID remains `warrior`). Camp captures and a twenty-three-view contact sheet at gameplay scale go under `artifacts/`. `tests/test_camp_interior.py` covers doors, fades, retained exterior position/camera, class/state preservation, inspection, Escape/pause, room bounds, deterministic art, actor isolation, audio/mute, and browser manifest inclusion. `tests/test_camp.py` covers services, gates, progression, migration, original art/audio determinism, channels, and camp rendering; existing combat tests explicitly launch expeditions. The campaign verifier departs from camp between regions and requires all nine boss captures plus final camp completion for every class. Browser staging includes `camp.py`, `camp_interior.py`, and all three audio loops; browser interactive/audio behavior still requires a real browser playtest.

Current camp limitations: only the Quartermaster storehouse is enterable. Other districts retain their existing services; there is no inventory, currency, crafting, or purchasing system. Porters and guards are decorative, non-colliding actors. The short supply hall suggests reserve rooms without making them traversable. Hub principles draw on compact preparation spaces, landmarks, service locations, short transitions, and a return-to-base rhythm familiar from Halls of Torment and the original PS2 Monster Hunter; all new camp art, names, composition, and audio are original. Automated headless captures cannot establish real-browser audio or input behavior.

## Assets and licenses


Existing imported assets retain their original handling. New regional assets are tightly cropped, palette-adapted runtime derivatives with integrated masonry/ripple accents; no source archive or full new pack is copied. Original license records remain under `assets/licenses/` and in their supplied directories. These are the terms recorded in the supplied license files, without inferred additional permissions.

| Assets | Creator / source | Recorded terms |
| --- | --- | --- |
| `assets/heroes/knight/` (generated locally; not in the public source repository) | Original helmeted derivatives rebuilt by `build_presentation.py` | Runtime-only curated frames; source license below applies |
| `assets/heroes/hero_knight/` (local dependency; not redistributed through GitHub) | [Sven Hero Knight](https://sventhole.itch.io/hero-knight) | Commercial/non-commercial game use permitted; redistribution on file-sharing sites prohibited. Exact supplied terms: `assets/licenses/HERO_KNIGHT_TERMS.txt` |
| `assets/heroes/ranger_source/`, `assets/heroes/ranger/` | [LuizMelo Martial Hero](https://luizmelo.itch.io/martial-hero); original hooded English woodland-ranger pixel derivatives | CC0; original `Martial Hero/License.txt` retained; `assets/licenses/RANGER_SOURCE_CC0.txt` |
| `assets/fonts/medievalsharp/` | MedievalSharp, Copyright (c) 2011 wmk69 (wmk69@o2.pl), Reserved Font Name MedievalSharp | SIL Open Font License 1.1; full `OFL.txt` retained; copy at `assets/licenses/MEDIEVALSHARP_OFL.txt` |
| `assets/fonts/pixeloperator/` | [Pixel Operator by Jayvee Enaguas / HarvettFox96](https://www.dafont.com/pixel-operator.font) | CC0 1.0 Universal; full supplied `LICENSE.txt` retained |
| `assets/ui/cruel-world-logo.png` | Original Cruel World composition generated by `build_presentation.py` / `ui.make_logo`, using MedievalSharp lettering | Original crown, blade ornament, bevel layers, crimson shadow and cracks; font remains under its retained OFL |
| `assets/heroes/wizard/` | [LuizMelo Wizard](https://luizmelo.itch.io/wizard-pack) | CC0 |
| `assets/enemies/luizmelo/` | [LuizMelo Monsters Creatures Fantasy](https://luizmelo.itch.io/monsters-creatures-fantasy) | CC0 |
| `assets/environments/legacy_fantasy/` | [Anokolisa Legacy Fantasy: High Forest](https://anokolisa.itch.io/sidescroller-pixelart-sprites-asset-pack-forest-16x16) | Commercial use/modification permitted; standalone source/modified asset sales require permission; attribution optional. See `assets/licenses/ANOKOLISA_TERMS.txt` |
| `assets/environments/moon_graveyard/` | [Anokolisa Hero’s Journey: Moon Graveyard](https://anokolisa.itch.io/moon-graveyard) | Same supplied Anokolisa terms |
| `assets/regions/water.png`, `falls.png` | [GandalfHardcore FREE 32x32 Overworld](https://gandalfhardcore.itch.io/free-pixel-art-sidescroller-asset-pack-32x32-overworld) | Commercial/non-commercial video games and projects; modification and display on designated websites allowed. No reselling/repackaging/redistributing assets, AI training, NFTs (Crypto/Blockchain/web3), game development tools, or printed materials. Exact supplied terms and selected crops: `assets/licenses/GANDALFHARDCORE_REGION_TERMS.txt`; retrieved October 6, 2026 |
| `assets/regions/cell.png`, `statue.png`, `pot.png`, `window.png`, `skeleton.png`, `cupboard.png` | [Hypnobius Grungy Dungeon Props #3](https://hypnobius.itch.io/grungy-dungeon-props) | Commercial (free/paid) and personal projects; modification allowed; credit optional. No reselling/redistributing original or modified pack, inclusion in other downloadable packs, NFTs/blockchain games, or AI training datasets. Exact supplied terms and selected crops: `assets/licenses/HYPNOBIUS_REGION_TERMS.txt`; retrieved October 6, 2026 |
| `assets/regions/forest-*.png`, `cave-*.png`, `graveyard-*.png` | Original Cruel World art generated by `build_region_assets.py` | Original deterministic compositions; imported transformed subsets are separate runtime strips above |
| `assets/audio/tommusic/` | [TomMusic Free Fantasy SFX and Music Bundle](https://tommusic.itch.io/free-fantasy-sfx-and-music-bundle) | Royalty-free commercial/non-commercial use; credit optional; no standalone pack resale/redistribution. See `assets/licenses/TOMMUSIC_TERMS.txt`. Credit: TomMusic |
| `assets/audio/sfx/` | [Brackeys / Asbjørn Thirslund](https://brackeysgames.itch.io/brackeys-platformer-bundle) | CC0; `assets/audio/BRACKEYS_LICENSE_AND_CREDITS.txt` |
| `assets/audio/music/Ironchest_dungeon*.ogg` | [Ironchest Games](https://ironchestgames.itch.io/ironchests-dungeon-music-loops) | CC0 v1.0 Universal; `assets/audio/IRONCHEST_LICENSE_AND_CREDITS.txt` |

Old knight/skeleton/dungeon sprites already tracked from the original prototype remain as legacy files and compatibility code, but are not loaded by the campaign renderer. Their bundled `assets/sprites/License.txt` links Craftpix terms; exact original pack provenance remains unverified. Additional unused imported source-pack material is excluded from new commits. The external DigitalDisco font is not loaded. MedievalSharp supplies headings/logo, PixelOperator supplies controls/body text. Missing or invalid custom fonts fall back to Pygame’s built-in font; missing/invalid logo regenerates the original composition safely. Preserve all existing records; do not redistribute raw imported packs as standalone downloads.


No repository-wide source-code license has been declared. Asset permissions are separate and governed by the retained records above.


## Progression and aftermath

First completed boss expeditions grant Sovereign Mycelium, Marauder Iron, and Lunar Remnant respectively. Schema 3 clears migrate into those permanent unlocks without fabricated expedition records. Replay clears award score and update records but never duplicate materials. Each class has three bounded fittings: healing efficiency, secondary recovery, and either mobility recovery or Ranger projectile reach. The Blacksmith uses one equipped slot per class. Press 1/2/3 to forge and equip an unlocked fitting, 0 to unequip, Esc to close. Forging is free once its material is held; materials are retained, so experimentation cannot exhaust them. Materials are proof of victory rather than consumable currency.

The storehouse counter offers exactly one provision (1/2/3): Field Dressing automatically heals 25 HP once when a living hero falls to 25% health; Warding Salt reduces environmental damage 25%, never enemy attacks; Hunters Charm adds 10% to optional discovery awards, never kills or breakable props. A fresh departure replenishes it. Checkpoint retry retains provision use, discovery claims, kill claims, and wave rewards; repeated kills cannot farm score or pickups. Expedition score resets on departure. Lifetime discoveries, class best scores, hero completion counts, and provision departure counts are recorded only on completion, atomically with the first-clear flag. Abandoned expeditions never enter the journal; existing legacy high scores remain preserved.

The Chronicler opens a regional journal: Left/Right selects a realm, unknown landmarks appear as ???, and completed discoveries, material ownership, class best scores, hero completions, and provision history remain visible. Service panels are opt-in and Esc closes them. NPC reactions change with clears, campaign completion, class, and recorded discoveries. Victories accumulate original geometric trophies in the courtyard; locked gates carry bars, available gates have green lamps, a confirmed gate is outlined as READIED, and cleared gates have gold lamps. The final victory adds a subtle warm courtyard tint and quieter courtyard ambience without changing collisions.

Gate confirmation begins a fixed-tick interstitial with the destination and one of twelve original camp sayings. A private shuffled quote pool never touches gameplay RNG. Simulation and gameplay input are gated during transitions; window focus loss suspends departure until focus returns, and Quit remains available. Title/class, doorway, and return scenes dissolve from the previous frame with no inserted black frame. Boss combat retains its readable existing health/title treatment; after the defeat animation and exit walk, results wait for Enter, showing first-clear/replay, material, score, discoveries, provision use, and unlocks. Return arrives beside the correct gate with full health. The final results are distinct and every cleared region remains replayable.

Audio keeps music and ambience independent. Deterministic 350 ms fade-out / 550 ms fade-in replaces changed loops at silence, rather than overlapping long decoded tracks on browser mixers; unchanged camp music retains playback phase. Repeated ambience requests do not reload or restart playback. Settings multiply fade gain and pause freezes fade time. This is deliberately a fade-through-silence alternative to overlapping crossfades for predictable pygbag channel behavior. No new sounds or imported asset changes are required.

`build_web.py` stages `progression.py` and all existing runtime assets. Browser saves remain session filesystem saves (durability across page reloads is not promised). Run `.venv/bin/python -m unittest discover -s tests`, `.venv/bin/python verify_campaign.py --output artifacts/progression-campaign`, and `.venv/bin/python capture_progression.py` for records, combat, and 800x600 camp/service/results/transition captures. Original aftermath visuals are deterministic runtime drawing. Real browser playback and human combat balance still require interactive playtesting.
