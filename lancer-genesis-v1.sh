#!/usr/bin/env bash
set -euo pipefail

base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
seed="${base}/genesis-complet-v1.gseed"
destination="${1:-${base}/Genesis-Wave-V1-restaure}"

[[ -f "${seed}" ]] || { echo "Seed absente : ${seed}" >&2; exit 1; }
[[ ! -e "${destination}" || -z "$(find "${destination}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]] || {
  echo "Destination non vide refusée : ${destination}" >&2
  exit 1
}

expected="$(awk '$2 == "genesis-complet-v1.gseed" {print $1}' "${base}/SHA256SUMS")"
observed="$(sha256sum "${seed}" | awk '{print $1}')"
[[ -n "${expected}" && "${expected}" == "${observed}" ]] || {
  echo "Échec d'intégrité SHA-256 de la seed" >&2
  exit 1
}

python3 "${base}/genesis_v1_core.py" restore --seed "${seed}" "${destination}"
echo "Genesis Wave V1 restauré dans : ${destination}"
echo "Lancement : python3 ${destination}/Genesis-Wave-App/genesis_wave_app.py"
