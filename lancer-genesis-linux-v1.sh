#!/usr/bin/env bash
set -euo pipefail

base="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
checksums="${base}/SHA256SUMS"
filename="genesis-complet-linux-v1.gwave"
destination="${1:-${base}/Genesis-GWave-Linux-V1-restaure}"
github_url="${GENESIS_GWAVE_URL:-https://raw.githubusercontent.com/roturoyetan-seed/Genesis-Seed-Originelle-Linux-V1/main/${filename}}"
cache="${base}/.genesis-cache/${filename}"

fail() { echo "Erreur Genesis : $*" >&2; exit 1; }
command -v python3 >/dev/null || fail "python3 est requis"
command -v sha256sum >/dev/null || fail "sha256sum est requis"
[[ -f "${checksums}" ]] || fail "SHA256SUMS absent"
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
python3 - "${cache}" "${destination}" <<'PY'
import bz2,hashlib,json,lzma,struct,sys,zlib
from pathlib import Path,PurePosixPath

source,destination=Path(sys.argv[1]),Path(sys.argv[2])
encoded=source.read_bytes();header=struct.Struct(">4sBBBBQQ32s")
if len(encoded)<header.size:raise SystemExit("GWAVE tronquée")
magic,version,transform,codec,flags,original_size,payload_size,expected=header.unpack(encoded[:header.size])
if magic!=b"GWV2" or version!=1 or flags or transform not in (1,2,3) or codec not in (0,1,2,3):raise SystemExit("GWAVE incompatible")
if original_size>2*1024**3:raise SystemExit("Budget d'expansion dépassé")
payload=encoded[header.size:]
if len(payload)!=payload_size:raise SystemExit("Longueur GWAVE incorrecte")
if codec==1:samples=zlib.decompress(payload)
elif codec==2:samples=lzma.decompress(payload)
elif codec==3:samples=bz2.decompress(payload)
else:samples=payload
if len(samples)!=original_size:raise SystemExit("Nombre d'échantillons incorrect")
data=bytearray(len(samples))
if samples:
 data[0]=samples[0]
 if transform==1:
  for i in range(1,len(samples)):data[i]=(data[i-1]+samples[i])&255
 elif transform==2:
  if len(samples)>1:data[1]=(data[0]+samples[1])&255
  for i in range(2,len(samples)):data[i]=(samples[i]+2*data[i-1]-data[i-2])&255
 else:
  for i in range(1,len(samples)):data[i]=data[i-1]^samples[i]
packed=bytes(data)
if hashlib.sha256(packed).digest()!=expected:raise SystemExit("Intégrité GWAVE incorrecte")
if packed[:5]!=b"GPAK1" or len(packed)<13:raise SystemExit("Conteneur Genesis invalide")
manifest_size=int.from_bytes(packed[5:13],"big");end=13+manifest_size
manifest=json.loads(packed[13:end]);cursor=end;root=destination.resolve();seen=set();root.mkdir(parents=True,exist_ok=True)
if manifest.get("format")!="GPAK1":raise SystemExit("Manifeste Genesis incompatible")
for entry in manifest.get("files",[]):
 relative=PurePosixPath(entry["path"])
 if relative.is_absolute() or not relative.parts or any(p in ("",".","..") for p in relative.parts) or str(relative) in seen:raise SystemExit("Chemin Genesis interdit")
 seen.add(str(relative));size=int(entry["size"]);content=packed[cursor:cursor+size];cursor+=size
 if len(content)!=size or hashlib.sha256(content).hexdigest()!=entry["sha256"]:raise SystemExit(f"Fichier corrompu : {relative}")
 target=(root/Path(*relative.parts)).resolve()
 if root not in target.parents:raise SystemExit("Sortie du dossier cible refusée")
 target.parent.mkdir(parents=True,exist_ok=True);partial=target.with_suffix(target.suffix+".partial");partial.write_bytes(content);partial.replace(target)
if cursor!=len(packed):raise SystemExit("Données supplémentaires dans la GWAVE")
print(f"{len(seen)} fichiers restaurés et vérifiés")
PY
echo "Genesis GWave Linux V1 restauré et vérifié dans : ${destination}"
echo "Lancement : python3 ${destination}/Genesis-Wave-App/genesis_wave_app.py"
