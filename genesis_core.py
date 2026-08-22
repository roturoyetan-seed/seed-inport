#!/usr/bin/env python3
"""Noyau sans perte Genesis MVP : fichiers <-> seed <-> nuage <-> fichiers."""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import math
import os
import re
import struct
import zlib
from pathlib import Path, PurePosixPath

PACK_MAGIC = b"GPAK1"
SEED_MAGIC = b"GSE1"
SEED_HEADER = struct.Struct(">4sBBQQ32s")
LEGACY_HEADER = struct.Struct(">4sBII32s")
POINT_RE = re.compile(r"^(\d+) x(-?\d+)y(-?\d+)z(-?\d+)$")
CODECS = {b"Z": "deflate", b"L": "lzma", b"B": "bzip2"}
RADIUS, INNER_RATIO, PATTERN_SCALE = 100_000, .08, 8
PHI = (1 + math.sqrt(5))/2
GOLDEN_ANGLE = math.pi*(3-math.sqrt(5))


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def safe_relative(path: str) -> PurePosixPath:
    clean = PurePosixPath(path)
    if clean.is_absolute() or not clean.parts or any(part in ("", ".", "..") for part in clean.parts):
        raise ValueError(f"Chemin interdit : {path!r}")
    return clean


def pack_directory(source: Path) -> bytes:
    source = source.resolve()
    if not source.is_dir():
        raise ValueError("La source doit être un dossier")
    entries, payload = [], bytearray()
    for path in sorted(source.rglob("*")):
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        if path.is_symlink():
            raise ValueError(f"Lien symbolique refusé : {path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source).as_posix()
        safe_relative(relative)
        data = path.read_bytes()
        entries.append({"path": relative, "size": len(data), "sha256": sha(data)})
        payload.extend(data)
    manifest = json.dumps({"format": "GPAK1", "files": entries}, ensure_ascii=False,
                          sort_keys=True, separators=(",", ":")).encode("utf-8")
    return PACK_MAGIC + len(manifest).to_bytes(8, "big") + manifest + payload


def unpack_directory(packed: bytes, destination: Path) -> list[Path]:
    if packed[:5] != PACK_MAGIC or len(packed) < 13:
        raise ValueError("Conteneur GPAK invalide")
    manifest_size = int.from_bytes(packed[5:13], "big")
    end = 13 + manifest_size
    manifest = json.loads(packed[13:end].decode("utf-8"))
    if manifest.get("format") != "GPAK1":
        raise ValueError("Version GPAK incompatible")
    destination.mkdir(parents=True, exist_ok=True)
    root = destination.resolve()
    cursor, restored, seen = end, [], set()
    for entry in manifest["files"]:
        relative = safe_relative(entry["path"])
        if str(relative) in seen:
            raise ValueError("Chemin en double dans le manifeste")
        seen.add(str(relative))
        size = int(entry["size"])
        data = packed[cursor:cursor+size]; cursor += size
        if len(data) != size or sha(data) != entry["sha256"]:
            raise ValueError(f"Intégrité incorrecte : {relative}")
        target = (root / Path(*relative.parts)).resolve()
        if target != root and root not in target.parents:
            raise ValueError("Tentative de sortie du dossier cible")
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(target.suffix + ".partial")
        partial.write_bytes(data); partial.replace(target); restored.append(target)
    if cursor != len(packed):
        raise ValueError("Données supplémentaires après le conteneur")
    return restored


def compress_once(data: bytes):
    candidates = [
        (b"Z", zlib.compress(data, 9)),
        (b"L", lzma.compress(data, format=lzma.FORMAT_XZ, preset=9)),
        (b"B", bz2.compress(data, 9)),
    ]
    return min(candidates, key=lambda item: len(item[1]))


def make_seed(packed: bytes, max_passes: int = 4) -> tuple[bytes, list[str]]:
    current, stages = packed, []
    for _ in range(max_passes):
        code, candidate = compress_once(current)
        if len(candidate) + 1 >= len(current):
            break
        current = candidate; stages.append(code)
    header = SEED_HEADER.pack(SEED_MAGIC, 1, len(stages), len(packed), len(current),
                              hashlib.sha256(packed).digest())
    seed = header + b"".join(stages) + current
    return seed, [CODECS[stage] for stage in stages]


def open_seed(seed: bytes) -> bytes:
    if len(seed) < SEED_HEADER.size:
        raise ValueError("Seed tronquée")
    magic, version, count, original_size, payload_size, digest = SEED_HEADER.unpack(seed[:SEED_HEADER.size])
    if magic != SEED_MAGIC or version != 1:
        raise ValueError("Format de seed incompatible")
    stages = list(seed[SEED_HEADER.size:SEED_HEADER.size+count])
    payload = seed[SEED_HEADER.size+count:]
    if len(payload) != payload_size:
        raise ValueError("Longueur de seed incorrecte")
    for stage in reversed(stages):
        if stage == ord("Z"): payload = zlib.decompress(payload)
        elif stage == ord("L"): payload = lzma.decompress(payload)
        elif stage == ord("B"): payload = bz2.decompress(payload)
        else: raise ValueError("Codec de seed inconnu")
    if len(payload) != original_size or hashlib.sha256(payload).digest() != digest:
        raise ValueError("Échec d'intégrité de la seed")
    return payload


def detect_seed_format(path: Path) -> str:
    magic = path.read_bytes()[:4]
    formats = {b"GSE1": "GSE1", b"GSD1": "GSD1", b"GML1": "GML1",
               b"GFR1": "GFR1", b"GDR1": "GDR1", b"GS2L": "GS2L"}
    if magic not in formats:
        raise ValueError(f"Signature de seed inconnue : {magic!r}")
    return formats[magic]


def open_legacy_gsd1(seed: bytes) -> bytes:
    if len(seed) < LEGACY_HEADER.size:
        raise ValueError("Seed GSD1 tronquée")
    magic, codec, original_size, payload_size, digest = LEGACY_HEADER.unpack(seed[:LEGACY_HEADER.size])
    payload = seed[LEGACY_HEADER.size:]
    if magic != b"GSD1" or codec != 1 or len(payload) != payload_size:
        raise ValueError("En-tête GSD1 invalide")
    data = zlib.decompress(payload, wbits=-15)
    if len(data) != original_size or hashlib.sha256(data).digest() != digest:
        raise ValueError("Échec d'intégrité GSD1")
    return data


def restore_any_seed(seed_path: Path, destination: Path):
    """Restaure automatiquement GSE1, GSD1 ou GML1 selon la signature."""
    kind = detect_seed_format(seed_path)
    destination.mkdir(parents=True, exist_ok=True)
    if kind == "GSE1":
        restored = unpack_directory(open_seed(seed_path.read_bytes()), destination)
        return {"format": kind, "files": [str(path) for path in restored]}
    if kind == "GSD1":
        data = open_legacy_gsd1(seed_path.read_bytes())
        suffix = ".bin"
        try:
            text = data.decode("utf-8")
            suffix = ".html" if "<html" in text.lower() else ".txt"
        except UnicodeDecodeError:
            pass
        target = destination/("reconstructed"+suffix)
        target.write_bytes(data)
        return {"format": kind, "files": [str(target)]}
    if kind == "GML1":
        from multilayer_genesis import expand
        report = expand(seed_path, destination, keep_clouds=True)
        return {"format": kind, "files": report["files"], "report": report}
    if kind == "GFR1":
        from multilayer_genesis import expand_formula
        report = expand_formula(seed_path, destination)
        return {"format": kind, "files": report["leaf_files"], "report": report}
    if kind == "GDR1":
        from seed_directory import expand
        return expand(seed_path, destination)
    raise ValueError("GS2L est une seed expérimentale de fichier unique non prise en charge par ce restaurateur")


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def dot(a, b): return sum(a[i]*b[i] for i in range(3))


def normalize(v):
    length = math.sqrt(dot(v, v)); return tuple(component/length for component in v)


def frame(position, count):
    y = 1-2*(position+.5)/count; horizontal = math.sqrt(max(0, 1-y*y)); angle = GOLDEN_ANGLE*position
    normal = normalize((math.cos(angle)*horizontal, y, math.sin(angle)*horizontal))
    depth = ((position+.5)/PHI) % 1
    radius = RADIUS*(INNER_RATIO**3+(1-INNER_RATIO**3)*depth)**(1/3)
    anchor = tuple(round(component*radius) for component in normal)
    reference = (0., 1., 0.) if abs(normal[1]) <= .98 else (1., 0., 0.)
    tangent = normalize(cross(reference, normal)); bitangent = normalize(cross(normal, tangent))
    return anchor, normal, tangent, bitangent


def local_motif(identifier, layer):
    z = layer*70; points = [(0, 0, z), (70, 0, z)]
    points.extend(((bit+1)*14, 22 if (identifier >> (3-bit)) & 1 else -22, z+14) for bit in range(4))
    return points


def global_motif(position, count, identifier, layer):
    anchor, normal, tangent, bitangent = frame(position, count)
    return [tuple(round(anchor[axis]+PATTERN_SCALE*(tangent[axis]*lx+bitangent[axis]*ly+normal[axis]*lz))
                  for axis in range(3)) for lx, ly, lz in local_motif(identifier, layer)]


def bytes_to_points(data: bytes, destination: Path, progress=None) -> int:
    partial = destination.with_suffix(destination.suffix + ".partial")
    number = 1
    with partial.open("w", encoding="ascii") as handle:
        for position, value in enumerate(data):
            for layer, identifier in enumerate((value >> 4, value & 15)):
                for x, y, z in global_motif(position, len(data), identifier, layer):
                    handle.write(f"{number} x{x}y{y}z{z}\n"); number += 1
            if progress and (position % 32 == 0 or position + 1 == len(data)):
                progress(position + 1, len(data))
    partial.replace(destination)
    return number-1


def parse_point(line: str, number: int):
    match = POINT_RE.fullmatch(line.rstrip("\n"))
    if not match or int(match.group(1)) != number:
        raise ValueError(f"Point incorrect à la ligne {number}")
    return tuple(map(int, match.groups()[1:]))


def points_to_bytes(source: Path) -> bytes:
    with source.open(encoding="ascii") as handle:
        line_count = sum(1 for _ in handle)
    if not line_count or line_count % 12:
        raise ValueError("Nombre de points invalide")
    count, result = line_count//12, bytearray()
    with source.open(encoding="ascii") as handle:
        number = 1
        for position in range(count):
            block = []
            for _ in range(12):
                block.append(parse_point(handle.readline(), number)); number += 1
            identifiers = []
            for layer, observed in ((0, block[:6]), (1, block[6:])):
                matches = [value for value in range(16) if observed == global_motif(position, count, value, layer)]
                if len(matches) != 1:
                    raise ValueError(f"Motif illisible à la position {position}")
                identifiers.append(matches[0])
            result.append((identifiers[0] << 4) | identifiers[1])
    return bytes(result)


def create_backup(source: Path, seed_path: Path, points_path: Path | None = None, progress=None):
    packed = pack_directory(source); seed, stages = make_seed(packed)
    seed_path.write_bytes(seed)
    point_count = bytes_to_points(packed, points_path, progress) if points_path else 0
    if progress and not points_path:
        progress(1, 1)
    return {"packed": len(packed), "seed": len(seed), "stages": stages, "points": point_count}


def restore_backup(seed_path: Path | None, points_path: Path | None, destination: Path):
    if bool(seed_path) == bool(points_path):
        raise ValueError("Choisir exactement une source : seed ou nuage")
    packed = open_seed(seed_path.read_bytes()) if seed_path else points_to_bytes(points_path)
    return unpack_directory(packed, destination)


def main():
    parser = argparse.ArgumentParser()
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create")
    create.add_argument("source", type=Path); create.add_argument("seed", type=Path); create.add_argument("--points", type=Path)
    restore = commands.add_parser("restore")
    group = restore.add_mutually_exclusive_group(required=True)
    group.add_argument("--seed", type=Path); group.add_argument("--points", type=Path)
    restore.add_argument("destination", type=Path)
    args = parser.parse_args()
    if args.command == "create": print(json.dumps(create_backup(args.source, args.seed, args.points), ensure_ascii=False))
    else: print(json.dumps([str(p) for p in restore_backup(args.seed, args.points, args.destination)], ensure_ascii=False))


if __name__ == "__main__": main()
