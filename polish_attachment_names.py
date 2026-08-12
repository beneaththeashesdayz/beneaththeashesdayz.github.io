from __future__ import annotations

import re
from pathlib import Path

CATALOGUE = Path(__file__).resolve().parent / "chernarus" / "traders" / "attachment-trader" / "catalogue-data.js"

LINE_RE = re.compile(
    r"^\{name:'(?P<name>(?:\\'|[^'])*)',className:'(?P<class>(?:\\'|[^'])*)',category:'(?P<category>(?:\\'|[^'])*)'(?P<rest>.*)$"
)

EXPLICIT = {
    "weaponcleaningkit": "Weapon Cleaning Kit",
    "ammo_40mm_chemgas": "40mm PO-X Grenade",
    "ammo_40mm_explosive": "40mm Explosive Grenade",
    "ammo_40mm_smoke_black": "40mm Smoke Grenade - Black",
    "ammo_40mm_smoke_green": "40mm Smoke Grenade - Green",
    "ammo_40mm_smoke_red": "40mm Smoke Grenade - Red",
    "ammo_40mm_smoke_white": "40mm Smoke Grenade - White",
}

TOKEN_LABELS = {
    "ak": "AK",
    "akm": "AKM",
    "ak74": "AK-74",
    "aks74u": "AKS-74U",
    "ar": "AR",
    "awm": "AWM",
    "buis": "BUIS",
    "cz": "CZ",
    "dmr": "DMR",
    "ekp": "EKP",
    "fal": "FAL",
    "g3": "G3",
    "hk": "HK",
    "k416": "K416",
    "m4": "M4",
    "m24": "M24",
    "m68": "M68",
    "m1911": "M1911",
    "m249": "M249",
    "m700": "M700",
    "m1014": "M1014",
    "mcx": "MCX",
    "mk14": "MK14",
    "mk47": "MK47",
    "mp5": "MP5",
    "mp5k": "MP5K",
    "mp7": "MP7",
    "mrds": "MRDS",
    "pkm": "PKM",
    "pmag": "PMAG",
    "pso": "PSO",
    "qbz": "QBZ",
    "qbz191": "QBZ-191",
    "ris": "RIS",
    "r93": "R93",
    "sks": "SKS",
    "sl7": "SL7",
    "stanag": "STANAG",
    "sv98": "SV-98",
    "svd": "SVD",
    "ump": "UMP",
    "vss": "VSS",
    "xm157": "XM157",
    "xm250": "XM250",
    "acog": "ACOG",
    "eotech": "EOTech",
    "hamr": "HAMR",
    "nightforce32x": "Nightforce 3-20x",
    "microt1": "Micro T-1",
    "sigsauertango": "SIG Sauer Tango",
    "trijiconskeetix": "Trijicon SKEETIR-X",
    "vortexspitfire": "Vortex Spitfire",
    "vortexstrikefire": "Vortex StrikeFire",
    "vortexuh1": "Vortex UH-1",
    "vortexvenom": "Vortex Venom",
    "osprey9": "Osprey 9",
}

CALIBERS = {
    "12g": "12 Gauge",
    "12gauge": "12 Gauge",
    "12gsteel": "12 Gauge Steel Shot",
    "22": ".22 LR",
    "277": ".277 Fury",
    "300blk": ".300 Blackout",
    "3006": ".30-06",
    "303": ".303 British",
    "308": ".308",
    "308win": ".308 Winchester",
    "338": ".338",
    "338lm": ".338 Lapua Magnum",
    "357": ".357 Magnum",
    "380": ".380 ACP",
    "408ct": ".408 CheyTac",
    "44mag": ".44 Magnum",
    "44magnum": ".44 Magnum",
    "45acp": ".45 ACP",
    "4570": ".45-70",
    "4630": "4.6x30mm",
    "50ae": ".50 AE",
    "50beo": ".50 Beowulf",
    "50bmg": ".50 BMG",
    "545x39": "5.45x39mm",
    "556": "5.56mm",
    "556x45": "5.56x45mm",
    "57x28": "5.7x28mm",
    "762x25": "7.62x25mm",
    "762x39": "7.62x39mm",
    "762x51": "7.62x51mm",
    "762x54": "7.62x54R",
    "792x33": "7.92x33mm",
    "9x19": "9x19mm",
    "9x39": "9x39mm",
}

TYPE_PREFIXES = {
    "optic": "Optic",
    "stock": "Stock",
    "handguard": "Handguard",
    "muzzle": "Muzzle Device",
    "barrel": "Barrel",
    "pisg": "Pistol Grip",
    "frog": "Foregrip",
    "other": "",
}


def js_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("'", "\\'")


def normalize_token(token: str) -> str:
    low = token.lower()
    if low in CALIBERS:
        return CALIBERS[low]
    if low in TOKEN_LABELS:
        return TOKEN_LABELS[low]

    capacity = re.fullmatch(r"(\d+)rnd", low)
    if capacity:
        return f"{capacity.group(1)}-Round"

    mag_capacity = re.fullmatch(r"(\d+)rndmag", low)
    if mag_capacity:
        return f"{mag_capacity.group(1)}-Round Magazine"

    # Split common model+capacity compounds such as vector_70rndmag after the
    # underscore pass, while keeping model numbers like M249 intact above.
    return token.capitalize()


def humanize_tokens(text: str) -> str:
    text = re.sub(r"(?<=[a-z])(?=[A-Z])", "_", text)
    text = text.replace("-", "_")
    tokens = [token for token in text.split("_") if token]
    return " ".join(normalize_token(token) for token in tokens).strip()


def polish_attachment_name(class_name: str, category: str) -> str:
    lower = class_name.lower()
    if lower in EXPLICIT:
        return EXPLICIT[lower]

    # My DF attachment class names carry a long implementation prefix followed
    # by the actual part type and model. Remove the scaffolding and put the part
    # type where a human would expect it.
    mydf_prefix = "my_df_weapons_attachments_"
    if lower.startswith(mydf_prefix):
        remainder = lower[len(mydf_prefix):]
        bits = remainder.split("_")
        part_type = bits.pop(0) if bits and bits[0] in TYPE_PREFIXES else ""
        model = humanize_tokens("_".join(bits))
        suffix = TYPE_PREFIXES.get(part_type, "")
        if suffix and suffix.lower() not in model.lower():
            return f"{model} {suffix}".strip()
        return model or humanize_tokens(remainder)

    # My DF ammunition and magazines use similarly verbose implementation paths.
    for prefix in (
        "my_df_weapons_ammo_",
        "my_df_weapons_rifles_",
        "my_df_weapons_snipers_",
        "my_df_weapons_smg_",
        "my_df_weapons_lmg_",
        "my_df_weapons_pistols_",
        "my_df_weapons_shotguns_",
    ):
        if lower.startswith(prefix):
            remainder = lower[len(prefix):]
            name = humanize_tokens(remainder)
            if "magazine" in category.lower() and "magazine" not in name.lower():
                name += " Magazine"
            return name

    # Harald's item prefixes are useful to the game, but noisy to players.
    for prefix in ("ha_magazine_", "ha_magazines_"):
        if lower.startswith(prefix):
            name = humanize_tokens(lower[len(prefix):])
            if "magazine" not in name.lower():
                name += " Magazine"
            return name
    if lower.startswith("ammo_ha_"):
        return humanize_tokens(lower[len("ammo_ha_"):])
    if lower.startswith("ha_optics_"):
        return f"{humanize_tokens(lower[len('ha_optics_'):])} Optic"
    if lower.startswith("ha_suppressor_"):
        return f"{humanize_tokens(lower[len('ha_suppressor_'):])} Suppressor"

    # Morty's ammo is much clearer once the mod prefix is removed.
    if lower.startswith("ttc_ammo_"):
        return humanize_tokens(lower[len("ttc_ammo_"):])

    # Vanilla shorthand cleanup.
    text = lower
    replacements = {
        "bttstck": "_buttstock",
        "hndgrd": "_handguard",
        "plastichandguard": "_plastic_handguard",
        "plastichndgrd": "_plastic_handguard",
        "railhndgrd": "_rail_handguard",
        "woodhndgrd": "_wood_handguard",
        "foldingbttstck": "_folding_buttstock",
        "plasticbttstck": "_plastic_buttstock",
        "woodbttstck": "_wood_buttstock",
        "stockbttstck": "_stock_buttstock",
        "cqbbttstck": "_cqb_buttstock",
        "mpbttstck": "_MP_buttstock",
        "oebttstck": "_OE_buttstock",
        "mphndgrd": "_MP_handguard",
        "rishndgrd": "_RIS_handguard",
        "optic": "_optic",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    name = humanize_tokens(text)
    name = re.sub(r"\bOptic Optic\b", "Optic", name)
    name = re.sub(r"\bButtstock Buttstock\b", "Buttstock", name)
    name = re.sub(r"\bHandguard Handguard\b", "Handguard", name)
    return name


def main() -> None:
    text = CATALOGUE.read_text(encoding="utf-8")
    output = []
    changed = 0

    for line in text.splitlines():
        match = LINE_RE.match(line)
        if not match:
            output.append(line)
            continue

        class_name = match.group("class").replace("\\'", "'")
        category = match.group("category").replace("\\'", "'")
        old_name = match.group("name").replace("\\'", "'")
        new_name = polish_attachment_name(class_name, category)
        if new_name and new_name != old_name:
            changed += 1
            line = "{name:'%s',className:'%s',category:'%s'%s" % (
                js_escape(new_name),
                match.group("class"),
                match.group("category"),
                match.group("rest"),
            )
        output.append(line)

    CATALOGUE.write_text("\n".join(output) + "\n", encoding="utf-8")
    print(f"Polished {changed} attachment trader display names.")


if __name__ == "__main__":
    main()
