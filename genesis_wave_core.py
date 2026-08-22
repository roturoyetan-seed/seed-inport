#!/usr/bin/env python3
"""Genesis Wave : fichiers <-> seed/onde <-> fichiers, sans perte.

Cette variante reprend l'architecture de Genesis MVP. Le conteneur GPAK1 et ses
protections restent identiques, mais la représentation géométrique par points est
remplacée par une suite d'échantillons d'onde différentielle.
"""

from __future__ import annotations

import argparse
import bz2
import hashlib
import json
import lzma
import struct
import zlib
from pathlib import Path

from genesis_core import pack_directory, unpack_directory

SEED_MAGIC = b"GWS1"
WAVE_MAGIC = b"GWV2"
VERSION = 1
MAX_OUTPUT = 2 * 1024**3
HEADER = struct.Struct(">4sBBBBQQ32s")

TRANSFORMS = {0: "amplitude-brute", 1: "onde-differentielle",
              2: "onde-acceleration", 3: "onde-xor"}
CODECS = {0: "aucun", 1: "deflate", 2: "lzma", 3: "bzip2"}


def digest(data: bytes) -> bytes:
    return hashlib.sha256(data).digest()


def wave_encode(data: bytes, transform: int = 1) -> bytes:
    """Convertit les octets en échantillons d'onde, de façon bijective."""
    if transform == 0 or not data:
        return data
    wave = bytearray(len(data)); wave[0] = data[0]
    if transform == 1:
        for index in range(1, len(data)):
            wave[index] = (data[index] - data[index - 1]) & 0xFF
    elif transform == 2:
        if len(data) > 1:
            wave[1] = (data[1] - data[0]) & 0xFF
        for index in range(2, len(data)):
            wave[index] = (data[index] - 2 * data[index - 1] + data[index - 2]) & 0xFF
    elif transform == 3:
        for index in range(1, len(data)):
            wave[index] = data[index] ^ data[index - 1]
    else:
        raise ValueError("Transformation d'onde inconnue")
    return bytes(wave)


def wave_decode(wave: bytes, transform: int = 1) -> bytes:
    if transform == 0 or not wave:
        return wave
    data = bytearray(len(wave)); data[0] = wave[0]
    if transform == 1:
        for index in range(1, len(wave)):
            data[index] = (data[index - 1] + wave[index]) & 0xFF
    elif transform == 2:
        if len(wave) > 1:
            data[1] = (data[0] + wave[1]) & 0xFF
        for index in range(2, len(wave)):
            data[index] = (wave[index] + 2 * data[index - 1] - data[index - 2]) & 0xFF
    elif transform == 3:
        for index in range(1, len(wave)):
            data[index] = wave[index] ^ data[index - 1]
    else:
        raise ValueError("Transformation d'onde inconnue")
    return bytes(data)


def compress(data: bytes, codec: int) -> bytes:
    if codec == 0: return data
    if codec == 1: return zlib.compress(data, 9)
    if codec == 2: return lzma.compress(data, preset=9)
    if codec == 3: return bz2.compress(data, 9)
    raise ValueError("Codec d'onde inconnu")


def decompress(payload: bytes, codec: int) -> bytes:
    if codec == 0: return payload
    if codec == 1: return zlib.decompress(payload)
    if codec == 2: return lzma.decompress(payload)
    if codec == 3: return bz2.decompress(payload)
    raise ValueError("Codec d'onde inconnu")


def make_wave(data: bytes, magic: bytes = WAVE_MAGIC) -> tuple[bytes, dict]:
    """Teste les formes d'onde et garde la représentation complète la plus petite."""
    candidates = []
    # Une seed peut conserver le signal brut si c'est optimal. Le fichier .gwave,
    # analogue au nuage .gen du MVP, doit en revanche contenir une vraie onde.
    transforms = TRANSFORMS if magic == SEED_MAGIC else (1, 2, 3)
    for transform in transforms:
        samples = wave_encode(data, transform)
        for codec in CODECS:
            payload = compress(samples, codec)
            candidates.append((len(payload), transform, codec, payload))
    _, transform, codec, payload = min(candidates, key=lambda item: item[0])
    encoded = HEADER.pack(magic, VERSION, transform, codec, 0, len(data), len(payload), digest(data)) + payload
    report = {"format": magic.decode("ascii"), "representation": TRANSFORMS[transform],
              "codec": CODECS[codec], "original_bytes": len(data), "encoded_bytes": len(encoded),
              "ratio": round(len(encoded) / max(1, len(data)), 6),
              "sha256": hashlib.sha256(data).hexdigest()}
    return encoded, report


def open_wave(encoded: bytes, expected_magic: bytes | None = None,
              maximum_output: int = MAX_OUTPUT) -> tuple[bytes, dict]:
    if len(encoded) < HEADER.size:
        raise ValueError("Onde Genesis tronquée")
    magic, version, transform, codec, flags, original_size, payload_size, expected = HEADER.unpack(encoded[:HEADER.size])
    if magic not in (SEED_MAGIC, WAVE_MAGIC) or (expected_magic and magic != expected_magic):
        raise ValueError("Signature d'onde Genesis inconnue")
    if version != VERSION or flags != 0 or transform not in TRANSFORMS or codec not in CODECS:
        raise ValueError("En-tête d'onde Genesis incompatible")
    if original_size > maximum_output:
        raise ValueError("Budget d'expansion de l'onde dépassé")
    payload = encoded[HEADER.size:]
    if len(payload) != payload_size:
        raise ValueError("Longueur de l'onde incorrecte")
    samples = decompress(payload, codec)
    if len(samples) != original_size:
        raise ValueError("Nombre d'échantillons incorrect")
    data = wave_decode(samples, transform)
    if digest(data) != expected:
        raise ValueError("Échec d'intégrité SHA-256 de l'onde")
    return data, {"format": magic.decode("ascii"), "representation": TRANSFORMS[transform],
                  "codec": CODECS[codec], "original_bytes": original_size,
                  "encoded_bytes": len(encoded), "sha256": expected.hex()}


def create_backup(source: Path, seed_path: Path, wave_path: Path | None = None) -> dict:
    packed = pack_directory(source)
    seed, seed_report = make_wave(packed, SEED_MAGIC)
    seed_path.parent.mkdir(parents=True, exist_ok=True); seed_path.write_bytes(seed)
    report = {"seed": seed_report, "wave": None}
    if wave_path:
        wave, wave_report = make_wave(packed, WAVE_MAGIC)
        wave_path.parent.mkdir(parents=True, exist_ok=True); wave_path.write_bytes(wave)
        report["wave"] = wave_report
    return report


def restore_backup(seed_path: Path | None, wave_path: Path | None,
                   destination: Path, maximum_output: int = MAX_OUTPUT) -> dict:
    if bool(seed_path) == bool(wave_path):
        raise ValueError("Choisir exactement une source : seed ou onde")
    source = seed_path or wave_path
    packed, report = open_wave(source.read_bytes(), SEED_MAGIC if seed_path else WAVE_MAGIC, maximum_output)
    report["files"] = [str(path) for path in unpack_directory(packed, destination)]
    return report


def inspect(path: Path, verify: bool = False) -> dict:
    encoded = path.read_bytes()
    if verify:
        _, report = open_wave(encoded); report["integrity"] = "valide"; return report
    if len(encoded) < HEADER.size:
        raise ValueError("Onde Genesis tronquée")
    magic, version, transform, codec, flags, original, payload, expected = HEADER.unpack(encoded[:HEADER.size])
    if magic not in (SEED_MAGIC, WAVE_MAGIC) or flags or transform not in TRANSFORMS or codec not in CODECS:
        raise ValueError("Onde Genesis invalide")
    return {"format": magic.decode(), "version": version, "representation": TRANSFORMS[transform],
            "codec": CODECS[codec], "original_bytes": original, "payload_bytes": payload,
            "sha256": expected.hex(), "integrity": "non vérifiée"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Genesis Wave — sauvegarde réversible par ondes")
    commands = parser.add_subparsers(dest="command", required=True)
    make = commands.add_parser("create", help="créer une seed et éventuellement son onde")
    make.add_argument("source", type=Path); make.add_argument("seed", type=Path)
    make.add_argument("--wave", type=Path, help="écrire aussi la représentation .gwave")
    restore = commands.add_parser("restore", help="restaurer depuis une seed ou une onde")
    group = restore.add_mutually_exclusive_group(required=True)
    group.add_argument("--seed", type=Path); group.add_argument("--wave", type=Path)
    restore.add_argument("destination", type=Path)
    show = commands.add_parser("inspect", help="afficher et éventuellement vérifier le fichier")
    show.add_argument("path", type=Path); show.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    if args.command == "create": report = create_backup(args.source, args.seed, args.wave)
    elif args.command == "restore": report = restore_backup(args.seed, args.wave, args.destination)
    else: report = inspect(args.path, args.verify)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
