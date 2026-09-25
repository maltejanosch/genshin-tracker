#!/usr/bin/env python3
"""Fetch the Enka.Network showcase for a UID and write a readable snapshot.

Usage:
    python scripts/enka.py                # uses UID from config below
    python scripts/enka.py --uid 123456789
    python scripts/enka.py --file data/enka/some.json   # parse a saved raw file

Outputs:
    data/enka/raw-YYYY-MM-DD.json   raw API response (history)
    data/enka/latest.md             human-readable build snapshot
Only characters in the in-game Character Showcase (with details on) are included.
"""
import argparse
import datetime as dt
import json
import pathlib
import urllib.request

UID = "762018318"
ROOT = pathlib.Path(__file__).resolve().parent.parent
ENKA_DIR = ROOT / "data" / "enka"
NAMES_FILE = ROOT / "data" / "names.json"  # manual overrides, extend as needed
STORE = "https://raw.githubusercontent.com/EnkaNetwork/API-docs/master/store/"
UA = {"User-Agent": "genshin-tracker/1.0 (personal use)"}

ELEMENT_BY_ENERGY = {"70": "Pyro", "71": "Electro", "72": "Hydro", "73": "Dendro",
                     "74": "Anemo", "75": "Cryo", "76": "Geo"}
DMG_BONUS = {"30": "Physical", "40": "Pyro", "41": "Electro", "42": "Hydro",
             "43": "Dendro", "44": "Anemo", "45": "Geo", "46": "Cryo"}
STAT_NAMES = {
    "FIGHT_PROP_HP": "HP", "FIGHT_PROP_HP_PERCENT": "HP%",
    "FIGHT_PROP_ATTACK": "ATK", "FIGHT_PROP_ATTACK_PERCENT": "ATK%",
    "FIGHT_PROP_DEFENSE": "DEF", "FIGHT_PROP_DEFENSE_PERCENT": "DEF%",
    "FIGHT_PROP_ELEMENT_MASTERY": "EM", "FIGHT_PROP_CHARGE_EFFICIENCY": "ER%",
    "FIGHT_PROP_CRITICAL": "CR%", "FIGHT_PROP_CRITICAL_HURT": "CD%",
    "FIGHT_PROP_HEAL_ADD": "Healing%", "FIGHT_PROP_PHYSICAL_ADD_HURT": "Physical DMG%",
    "FIGHT_PROP_FIRE_ADD_HURT": "Pyro DMG%", "FIGHT_PROP_ELEC_ADD_HURT": "Electro DMG%",
    "FIGHT_PROP_WATER_ADD_HURT": "Hydro DMG%", "FIGHT_PROP_GRASS_ADD_HURT": "Dendro DMG%",
    "FIGHT_PROP_WIND_ADD_HURT": "Anemo DMG%", "FIGHT_PROP_ROCK_ADD_HURT": "Geo DMG%",
    "FIGHT_PROP_ICE_ADD_HURT": "Cryo DMG%",
}
SLOTS = {"EQUIP_BRACER": "Flower", "EQUIP_NECKLACE": "Plume", "EQUIP_SHOES": "Sands",
         "EQUIP_RING": "Goblet", "EQUIP_DRESS": "Circlet"}


def get_json(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)


def load_names():
    chars, loc = {}, {}
    try:
        chars = get_json(STORE + "characters.json")
        loc = get_json(STORE + "loc.json").get("en", {})
    except Exception as e:  # works offline too, just with fewer names
        print(f"warning: could not load Enka name store ({e})")
    overrides = json.loads(NAMES_FILE.read_text()) if NAMES_FILE.exists() else {}
    return chars, loc, overrides


def char_name(avatar, chars, loc, overrides):
    aid = str(avatar["avatarId"])
    if aid in overrides.get("characters", {}):
        return overrides["characters"][aid]
    if aid in ("10000005", "10000007"):
        element = next((ELEMENT_BY_ENERGY[k] for k in avatar["fightPropMap"]
                        if k in ELEMENT_BY_ENERGY), "?")
        return f"Traveler ({element})"
    h = str(chars.get(aid, {}).get("NameTextMapHash", ""))
    return loc.get(h, f"Unknown {aid}")


def item_name(flat, loc, overrides):
    icon = flat.get("icon", "")
    if icon in overrides.get("weapons", {}):
        return overrides["weapons"][icon]
    return loc.get(str(flat.get("nameTextMapHash")), icon.replace("UI_EquipIcon_", ""))


def fmt(stat, value):
    name = STAT_NAMES.get(stat, stat)
    return f"{name} {value:g}" if "%" in name else f"{name} {int(value)}"


def talents(avatar, chars):
    info = chars.get(f"{avatar['avatarId']}-{avatar.get('skillDepotId')}") \
        or chars.get(str(avatar["avatarId"]), {})
    order = info.get("SkillOrder") or []
    if not all(str(sid) in avatar["skillLevelMap"] for sid in order) or not order:
        order = sorted(avatar["skillLevelMap"], key=int)[:3]
    proud = info.get("ProudMap", {})
    extra = avatar.get("proudSkillExtraLevelMap", {})
    out = []
    for sid in order:
        base = avatar["skillLevelMap"].get(str(sid), 1)
        bonus = extra.get(str(proud.get(str(sid), "")), 0)
        out.append(f"{base}" + (f" (+{bonus})" if bonus else ""))
    return " / ".join(out)


def render(data, chars, loc, overrides):
    p = data["playerInfo"]
    today = dt.date.today().isoformat()
    lines = [f"# Enka snapshot {today}", "",
             f"{p.get('nickname')} · UID {data.get('uid')} · AR {p.get('level')} · "
             f"WL {p.get('worldLevel')} · Abyss {p.get('towerFloorIndex')}-{p.get('towerLevelIndex')} "
             f"({p.get('towerStarIndex')}★)", ""]
    for av in data.get("avatarInfoList", []):
        fp = av["fightPropMap"]
        cons = len(av.get("talentIdList", []))
        level = av["propMap"]["4001"]["val"]
        lines.append(f"## {char_name(av, chars, loc, overrides)} (Lv {level}, C{cons})")
        bonus = [f"{DMG_BONUS[k]} {fp[k]*100:.1f}%" for k in DMG_BONUS if fp.get(k)]
        lines.append(
            f"- Stats: HP {fp.get('2000', 0):.0f} · ATK {fp.get('2001', 0):.0f} · DEF {fp.get('2002', 0):.0f} · "
            f"EM {fp.get('28', 0):.0f} · CR {fp.get('20', 0)*100:.1f}% · CD {fp.get('22', 0)*100:.1f}% · "
            f"ER {fp.get('23', 0)*100:.1f}%" + (" · " + ", ".join(bonus) if bonus else ""))
        lines.append(f"- Talents (NA / Skill / Burst): {talents(av, chars)}")
        sets, arts = {}, []
        for eq in av.get("equipList", []):
            flat = eq["flat"]
            if "weapon" in eq:
                w = eq["weapon"]
                ref = next(iter(w.get("affixMap", {}).values()), 0) + 1
                lines.append(f"- Weapon: {item_name(flat, loc, overrides)} {flat['rankLevel']}★ "
                             f"Lv {w['level']} R{ref}")
            else:
                s = loc.get(str(flat.get("setNameTextMapHash")), "?")
                sets[s] = sets.get(s, 0) + 1
                main = flat["reliquaryMainstat"]
                subs = ", ".join(fmt(x["appendPropId"], x["statValue"])
                                 for x in flat.get("reliquarySubstats", []))
                arts.append(f"  - {SLOTS.get(flat['equipType'], '?')} {flat['rankLevel']}★ "
                             f"+{eq['reliquary']['level'] - 1}: "
                             f"{fmt(main['mainPropId'], main['statValue'])} | {subs}")
        if sets:
            lines.append("- Artifacts: " + ", ".join(f"{n}pc {s}" for s, n in sets.items()))
            lines.extend(arts)
        lines.append("")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--uid", default=UID)
    ap.add_argument("--file", help="parse a saved raw JSON instead of fetching")
    args = ap.parse_args()
    ENKA_DIR.mkdir(parents=True, exist_ok=True)
    if args.file:
        data = json.loads(pathlib.Path(args.file).read_text())
    else:
        data = get_json(f"https://enka.network/api/uid/{args.uid}")
        raw = ENKA_DIR / f"raw-{dt.date.today().isoformat()}.json"
        raw.write_text(json.dumps(data, indent=1, ensure_ascii=False))
        print(f"saved {raw.relative_to(ROOT)}")
    out = ENKA_DIR / "latest.md"
    out.write_text(render(data, *load_names()))
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
