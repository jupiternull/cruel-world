# Cruel World

**A playable pixel-art dark-fantasy action alpha:** three heroes, three side-scrolling realms, and three bosses in a complete keyboard-driven campaign.

![Cruel World title screen](docs/media/title.png)

**[Play the closed alpha in your browser](https://jupiternull.github.io/cruel-world/)** — desktop keyboard required.

> **Alpha status:** Combat, balance, performance, and presentation are still evolving. The current campaign is playable on desktop and through the live GitHub Pages HTML5 build. A restricted itch.io playtest page is still planned. Camp, crafting, character creation, and expedition systems are planned.

## Playable today

- Knight, Ranger, and Wizard with distinct attacks, abilities, and defensive movement.
- Three authored realms with platforms, ladders, hazards, checkpoints, finite enemy waves, and telegraphed bosses.
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

![Campaign victory](docs/media/victory.png)

These are current runtime captures, including boss encounters, rather than concept art. Imported and derived art supports the alpha; custom original pixel art is part of the longer-term plan.

## Run locally

Python 3.10+ and Pygame 2.6.1+; interactive play requires a graphical desktop.

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

The public source repository does not redistribute the Hero Knight source pack or its generated runtime derivatives. For a complete local source checkout, download Hero Knight from the creator's page listed under [Assets and licenses](#assets-and-licenses), place the supplied `Hero Knight` directory at `assets/heroes/hero_knight/Hero Knight/`, then run `python build_presentation.py` before launching. Published playtest builds include the required runtime character data as part of the packaged game.

Choose **Begin campaign**, select a hero, and press Enter. Continue right, clear two finite waves per realm (five then six enemies, at most four alive), defeat the solo boss, and enter the glowing door. Complete all three realms to win.

## Browser build

Live build: **https://jupiternull.github.io/cruel-world/**

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
| E | Class secondary ability |
| Shift or Q | Dash/evade/blink with brief invulnerability |
| Escape or P | Pause/resume |
| Up/Down or W/S; Enter/Space | Navigate and select menu items |
| Left/Right | Select class; adjust selected setting |
| Escape in class/settings/death | Return to preceding menu/title |
| R after death | Restart campaign with current class |

Pause offers resume, settings, restart with class selection, and title. **Retry checkpoint** restores health at the reached flag, resets the current battle, and deducts 250 points (minimum zero). Restart begins in the forest. Losing focus pauses play; menus and pause freeze simulation, projectiles, cooldowns, and progression.

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
| Verdant Ruins | Mossy ruins, bridges, short ladders; goblins and flying eyes | Spore Sovereign: leave marked bursts and avoid alternating spore volleys |
| Sunken Keep | Interior walls, wooden ledges, deep ladder shafts; mushrooms and shield skeletons | Iron Marauder: armored front, sweep, lunge, shockwave; punish rear, windup, or recovery |
| Moon Graveyard | Mausoleums, columns, high graveyard perches; goblins, mushrooms, shield skeletons | Moon Eater: falling moon columns and diagonal shots; reposition and aim or jump into melee range |

Orange markers and translucent red areas warn of attacks. Frontal armor reduces damage to one third outside enemy windup/recovery; rear attacks and arcane waves bypass it. Gates prevent skipping battles. Raised platforms are one-way. Hazards deal 16 damage; wave clears heal 15 HP, boss clears 30 HP, realm transitions 40 HP, and health pickups 30 HP.

## Feedback

Use GitHub Issues with the **Bug report** or **Playtest feedback** template. Include OS/browser, class, realm/wave, reproduction steps, and screenshots or video where useful. Feedback on attack commitment, dodge timing, readability, difficulty spikes, navigation, audio, and browser performance is especially useful. See [PLAYTEST.md](PLAYTEST.md) for browser caveats.

## Roadmap — planned

These are development directions, not shipped features or dated promises.

- **Next alpha:** restricted itch.io deployment, broader desktop/browser playtesting, balance and readability passes, performance and input-feel fixes.
- **Character identity:** controlled character creation, expanded class selection, and subclasses with distinct roles and tradeoffs.
- **Base camp:** a compact roamable hub with NPCs, services, training, crafting, and persistent camp progression.
- **Expeditions and progression:** prepare at camp, undertake expeditions, master bosses, collect materials, and develop equipment and camp services.
- **World and art:** custom original pixel art, richer NPC and faction relationships, and deeper lore supplied later by the creator. Current names and encounters do not establish future lore canon.
- **Optional exploration:** evaluate procedural expeditions assembled from authored chunks while retaining intentional encounter design and readable traversal.

## Long-term vision

Cruel World is intended to grow into a side-scrolling pixel-art dark-fantasy action RPG. Design influences are principles: deliberate Soulslike combat and environmental storytelling; Monster Hunter-style preparation, boss mastery, and material progression; and MMO-like class identity, factions, and NPC world depth. These influences describe the intended experience; multiplayer is not a current feature or a commitment.

The planned rhythm is a living camp, purposeful preparation, dangerous expeditions, and lasting progression. Story and lore will be developed later rather than filled in with invented canon here.

## Development and verification

Simulation runs at a fixed 60 Hz, independently of rendering. `main.py` handles events and menus; `campaign.py` owns authored traversal/progression; `entities/hero.py` and `entities/monster.py` implement combat. `camera.py`, `projectile.py`, `scenery.py`, `ui.py`, `audio.py`, and `persistence.py` support rendering and services.

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py assets.py audio.py camera.py campaign.py projectile.py scenery.py config.py game_state.py persistence.py ui.py level.py entities tests build_web.py build_presentation.py capture_presentation.py capture_gameplay.py verify_campaign.py
git diff --check
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy CRUELWORLD_SAVE_PATH=/tmp/cruel-smoke.json python main.py --class wizard --environment 3 --frames 120 --screenshot /tmp/cruel-smoke.png
python verify_campaign.py --ticks 60000 --output /tmp/cruel-campaign-verification
```

`--class` starts directly in gameplay; `--environment 1|2|3` selects a debug realm; `--frames` bounds rendering; `--screenshot` saves the final frame. Without `--class`, play starts at the title. The campaign verifier uses ordinary attacks and checkpoint retries, captures all nine class/realm bosses, and fails unless every class wins with at most five retries. Bots supplement desktop/browser playtesting.

`capture_presentation.py` captures menus and class/realm views into ignored development output. To regenerate the continuous gameplay GIF, install Pillow (`python -m pip install Pillow`) and run `python capture_gameplay.py`; frames stay in memory and saves use a temporary directory. `build_presentation.py` deterministically rebuilds curated Knight/Ranger derivatives and the logo without changing source packs.

Desktop saves use atomic schema-versioned storage at `$XDG_DATA_HOME/cruelworld/save.json` or `~/.local/share/cruelworld/save.json`; override with `CRUELWORLD_SAVE_PATH` for isolated testing. Saves retain high score, settings, selected class, and furthest realm, not a resumable run. Legacy scores/settings and `huntress` IDs migrate safely. Corrupt values default safely; write errors appear in the UI. Missing audio degrades to fallbacks; required invalid sprites cause a clear startup error.

## Assets and licenses


The imported subset is used directly; no source archive is copied. Original license records remain under `assets/licenses/` and in their supplied directories. These are the terms recorded in the supplied license files, without inferred additional permissions.

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
| `assets/audio/tommusic/` | [TomMusic Free Fantasy SFX and Music Bundle](https://tommusic.itch.io/free-fantasy-sfx-and-music-bundle) | Royalty-free commercial/non-commercial use; credit optional; no standalone pack resale/redistribution. See `assets/licenses/TOMMUSIC_TERMS.txt`. Credit: TomMusic |
| `assets/audio/sfx/` | [Brackeys / Asbjørn Thirslund](https://brackeysgames.itch.io/brackeys-platformer-bundle) | CC0; `assets/audio/BRACKEYS_LICENSE_AND_CREDITS.txt` |
| `assets/audio/music/Ironchest_dungeon*.ogg` | [Ironchest Games](https://ironchestgames.itch.io/ironchests-dungeon-music-loops) | CC0 v1.0 Universal; `assets/audio/IRONCHEST_LICENSE_AND_CREDITS.txt` |

Old knight/skeleton/dungeon sprites already tracked from the original prototype remain as legacy files and compatibility code, but are not loaded by the campaign renderer. Their bundled `assets/sprites/License.txt` links Craftpix terms; exact original pack provenance remains unverified. Additional unused imported source-pack material is excluded from new commits. The external DigitalDisco font is not loaded. MedievalSharp supplies headings/logo, PixelOperator supplies controls/body text. Missing or invalid custom fonts fall back to Pygame’s built-in font; missing/invalid logo regenerates the original composition safely. Preserve all existing records; do not redistribute raw imported packs as standalone downloads.


No repository-wide source-code license has been declared. Asset permissions are separate and governed by the retained records above.
