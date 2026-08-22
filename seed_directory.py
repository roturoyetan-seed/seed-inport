#!/usr/bin/env python3
"""GDR1 : seed/nuage répertoire reconstruisant un catalogue de seeds enfants."""

from __future__ import annotations

import argparse
import hashlib
import json
import lzma
import struct
from pathlib import Path

from genesis_core import bytes_to_points, points_to_bytes

MAGIC = b"GDR1"
HEADER = struct.Struct(">4sQQ32s")


def _safe_name(name):
    if not name or Path(name).name != name or name in (".", ".."):
        raise ValueError(f"Nom de seed interdit : {name!r}")
    return name


def create_directory(source, destination, points=None):
    seeds = sorted(path for path in source.iterdir() if path.is_file() and path.suffix == ".gseed")
    if not seeds:
        raise ValueError("Le répertoire ne contient aucune seed")
    payload, entries, blocks = bytearray(), [], {}
    logical_bytes = 0
    for path in seeds:
        data = path.read_bytes()
        _safe_name(path.name)
        logical_bytes += len(data)
        sha = hashlib.sha256(data).hexdigest()
        if sha in blocks:
            offset, size = blocks[sha]
        else:
            offset, size = len(payload), len(data)
            payload.extend(data); blocks[sha] = (offset, size)
        entries.append({"name":path.name,"offset":offset,"size":size,
                        "sha256":sha,"magic":data[:4].decode("ascii", "replace")})
    catalog = json.dumps({"format":"Genesis-Seed-Directory-1","count":len(entries),
                          "entries":entries}, ensure_ascii=False, sort_keys=True,
                         separators=(",", ":")).encode()
    raw = len(catalog).to_bytes(8, "big") + catalog + payload
    compressed = lzma.compress(raw, preset=9)
    container = HEADER.pack(MAGIC, len(raw), len(compressed), hashlib.sha256(raw).digest()) + compressed
    destination.write_bytes(container)
    point_count = bytes_to_points(container, points) if points else 0
    return {"children":len(entries),"logical_children_bytes":logical_bytes,
            "unique_blocks":len(blocks),"stored_children_bytes":len(payload),
            "directory_seed":len(container),"points":point_count}


def open_directory(data):
    if len(data) < HEADER.size:
        raise ValueError("GDR1 tronqué")
    magic, raw_size, packed_size, digest = HEADER.unpack(data[:HEADER.size])
    packed = data[HEADER.size:]
    if magic != MAGIC or len(packed) != packed_size:
        raise ValueError("En-tête GDR1 invalide")
    raw = lzma.decompress(packed)
    if len(raw) != raw_size or hashlib.sha256(raw).digest() != digest:
        raise ValueError("Intégrité GDR1 incorrecte")
    catalog_size = int.from_bytes(raw[:8], "big")
    catalog = json.loads(raw[8:8+catalog_size].decode())
    if catalog.get("format") != "Genesis-Seed-Directory-1":
        raise ValueError("Catalogue GDR1 incompatible")
    return catalog, raw[8+catalog_size:]


def expand(source, destination, from_points=False):
    data = points_to_bytes(source) if from_points else source.read_bytes()
    catalog, payload = open_directory(data)
    destination.mkdir(parents=True, exist_ok=True)
    restored = []
    for entry in catalog["entries"]:
        name = _safe_name(entry["name"])
        offset, size = int(entry["offset"]), int(entry["size"])
        child = payload[offset:offset+size]
        if len(child) != size or hashlib.sha256(child).hexdigest() != entry["sha256"]:
            raise ValueError(f"Seed enfant corrompue : {name}")
        target = destination / name
        target.write_bytes(child); restored.append(str(target))
    (destination/"catalog.json").write_text(json.dumps(catalog, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    return {"format":"GDR1","children":len(restored),"files":restored}


def main():
    parser = argparse.ArgumentParser(); commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create"); create.add_argument("source", type=Path)
    create.add_argument("seed", type=Path); create.add_argument("--points", type=Path)
    run = commands.add_parser("expand"); run.add_argument("source", type=Path); run.add_argument("destination", type=Path)
    run.add_argument("--points", action="store_true")
    args = parser.parse_args()
    result = create_directory(args.source, args.seed, args.points) if args.command == "create" else expand(args.source, args.destination, args.points)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
