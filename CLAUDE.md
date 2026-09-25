# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# Genshin Impact tracker – instructions for Claude

This repo tracks Malte's Genshin Impact account. Keep it current; it replaces fetching everything again.

## Account
- UID 762018318 (EU), in-game name YakaMono
- Enka raw data: https://enka.network/api/uid/762018318 (only characters in the in-game showcase)
- Akasha: https://akasha.cv/profile/762018318 – leaderboard ranks + crit value; keeps every character ever
  showcased (not just the current showcase). Cloudflare blocks curl, so read it via the browser.

## Commands
Python 3.9+, standard library only. No tests or linter.
```bash
python scripts/enka.py                                   # fetch showcase → raw-<today>.json + latest.md
python scripts/enka.py --file data/enka/raw-DATE.json    # re-render latest.md from a saved raw file (no API call)
python scripts/enka.py --uid 123456789                   # another account
```
After editing `data/names.json`, re-render with `--file` instead of fetching again.

## How `scripts/enka.py` resolves names
- Character/weapon/artifact-set names come from the Enka store on GitHub (`characters.json`, `loc.json`),
  fetched on every run. If that fails the script still runs, but names fall back to icon names / `Unknown <id>`.
- `data/names.json` overrides win over the store:
  - `"weapons"` keyed by the **full** icon name, including the `UI_EquipIcon_` prefix
    (latest.md shows it without the prefix, e.g. `Sword_Mitsurugi` → key `UI_EquipIcon_Sword_Mitsurugi`).
  - `"characters"` keyed by the numeric `avatarId` as a string.
  - `"sets"` keyed by the artifact set ID (from the icon, e.g. `UI_RelicIcon_15020_4` → `15020`).
    Unknown sets render as `Set <id>`.
- The Enka store is often behind on new characters/weapons/sets; https://gi.yatta.moe/api/v2/en/weapon
  and `/reliquary` resolve names by icon or set ID.
- Traveler (avatarId 10000005/10000007) is named by element, derived from `fightPropMap`.

## Files
- `data/roster.md` – every owned character with level and constellation (source: HoYoLAB screenshots). Written in German.
- `data/builds.md` – curated build notes per character: current gear, what to fix, priorities
- `data/weapons.md` – weapon inventory (screenshots, cross-checked with Enka); unused weapons = upgrade options
- `data/teams.md` – planned teams, status, what's missing; header also records the game version
- `data/enka/latest.md` – generated snapshot, do not hand-edit
- `data/enka/raw-*.json` – raw Enka responses (history); one per day, a same-day rerun overwrites it
- `data/names.json` – manual name overrides for weapons/characters the Enka store can't resolve

## Workflows
- **"Refresh builds"**: run `python scripts/enka.py`, compare `data/enka/latest.md` with `data/builds.md`,
  update build notes, report what changed, then commit.
- **Roster update** (screenshots or "X is now Lv 80"): edit `data/roster.md`, commit.
- **Team/pull advice**: read roster, builds and teams first. Check current version, banners and meta
  on the web before advising – game info changes every 6 weeks.
- If a weapon shows as an icon name (e.g. `Sword_WeaponQuestSnezhnaya`), look up the real name and add it
  to `data/names.json` (with the `UI_EquipIcon_` prefix), then re-render.

## Conventions
- Update the "Stand" date at the top of any file you change (format `DD.MM.YYYY`).
- Keep each file in its existing language (roster German, builds/teams English).
- Commit after every update with a short message (e.g. `builds: Bennett weapon Lv 90`) and push.
- Reply to Malte in the language he writes in.
