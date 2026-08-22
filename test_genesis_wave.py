#!/usr/bin/env python3
import json
import tempfile
import unittest
from pathlib import Path

from genesis_wave_core import (HEADER, SEED_MAGIC, WAVE_MAGIC, create_backup, inspect,
                               make_wave, open_wave, restore_backup, wave_decode, wave_encode)


class GenesisWaveTests(unittest.TestCase):
    def test_all_wave_transforms_are_reversible(self):
        samples = bytes(range(256)) + b"onde sinusoidale" * 50
        for transform in range(4):
            self.assertEqual(wave_decode(wave_encode(samples, transform), transform), samples)

    def test_directory_roundtrip_from_seed_and_wave(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; (source / "sub").mkdir(parents=True)
            (source / "bonjour.txt").write_text("Une onde Genesis\n" * 1000, encoding="utf-8")
            (source / "sub" / "config.json").write_text(json.dumps({"onde": True}), encoding="utf-8")
            seed, wave = root / "backup.gseed", root / "backup.gwave"
            report = create_backup(source, seed, wave)
            self.assertEqual(report["seed"]["format"], "GWS1")
            self.assertNotEqual(report["wave"]["representation"], "amplitude-brute")
            self.assertEqual(inspect(wave, True)["integrity"], "valide")
            for kind, path in (("seed", seed), ("wave", wave)):
                target = root / ("restore-" + kind)
                restore_backup(path if kind == "seed" else None, path if kind == "wave" else None, target)
                self.assertEqual((target / "bonjour.txt").read_bytes(), (source / "bonjour.txt").read_bytes())
                self.assertEqual((target / "sub" / "config.json").read_bytes(),
                                 (source / "sub" / "config.json").read_bytes())

    def test_corruption_is_rejected(self):
        encoded, _ = make_wave(b"test" * 1000, WAVE_MAGIC)
        damaged = bytearray(encoded); damaged[-1] ^= 1
        with self.assertRaises(Exception): open_wave(bytes(damaged))

    def test_expansion_budget_is_enforced(self):
        encoded, _ = make_wave(b"x" * 100, SEED_MAGIC)
        with self.assertRaises(ValueError): open_wave(encoded, maximum_output=99)

    def test_unknown_header_is_rejected(self):
        fake = HEADER.pack(b"NOPE", 1, 0, 0, 0, 0, 0, bytes(32))
        with self.assertRaises(ValueError): open_wave(fake)


if __name__ == "__main__": unittest.main()
