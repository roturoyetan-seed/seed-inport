#!/usr/bin/env bash
set -euo pipefail

base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
core="${base}/genesis_wave_core.py"
checksums="${base}/SHA256SUMS"
filename="genesis-complet-v1.gwave"
destination="${1:-${base}/Genesis-GWave-V1-restaure}"
github_url="${GENESIS_GWAVE_URL:-https://raw.githubusercontent.com/roturoyetan-seed/Genesis-Seed-Originelle-V1/main/${filename}}"
cache="${base}/.genesis-cache/${filename}"

fail() { echo "Erreur Genesis : $*" >&2; exit 1; }
command -v python3 >/dev/null || fail "python3 est requis"
command -v sha256sum >/dev/null || fail "sha256sum est requis"
[[ -f "${core}" && -f "${checksums}" ]] || fail "lanceur incomplet"
[[ ! -e "${destination}" || -z "$(find "${destination}" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ]] || fail "destination non vide refusée : ${destination}"

expected="$(awk -v name="${filename}" '$2 == name {print $1}' "${checksums}")"
[[ "${expected}" =~ ^[0-9a-f]{64}$ ]] || fail "empreinte GWAVE absente de SHA256SUMS"
if [[ "${GENESIS_ALLOW_LOCAL_SOURCE:-0}" != "1" ]]; then
  [[ "${github_url}" == https://raw.githubusercontent.com/* ]] || fail "seule une source HTTPS raw.githubusercontent.com est autorisée"
fi

mkdir -p "$(dirname "${cache}")"
if [[ ! -f "${cache}" ]] || [[ "$(sha256sum "${cache}" | awk '{print $1}')" != "${expected}" ]]; then
  partial="${cache}.partial"
  if command -v curl >/dev/null; then
    curl --fail --location --proto '=https,file' --tlsv1.2 --output "${partial}" "${github_url}"
  elif command -v wget >/dev/null && [[ "${github_url}" == https://* ]]; then
    wget --https-only --output-document="${partial}" "${github_url}"
  else
    fail "curl est requis (ou wget pour HTTPS)"
  fi
  printf '%s  %s\n' "${expected}" "${partial}" | sha256sum -c - >/dev/null || fail "empreinte GWAVE invalide"
  mv "${partial}" "${cache}"
fi

printf '%s  %s\n' "${expected}" "${cache}" | sha256sum -c - >/dev/null || fail "cache GWAVE corrompu"
python3 "${core}" restore --wave "${cache}" "${destination}"
echo "Genesis GWave V1 restauré et vérifié dans : ${destination}"
echo "Lancement : python3 ${destination}/Genesis-Wave-App/genesis_wave_app.py"
