#!/usr/bin/env bash
# Comprueba que GitHub y GitLab tienen exactamente las mismas ramas y etiquetas.
# No necesita credenciales si los repositorios son publicos.
set -euo pipefail

GH_REPO="${GH_REPO:-https://github.com/BENDER35/ftp-lab.git}"
GL_REPO="${GL_REPO:-https://gitlab.com/BENDER_5000/ftp-lab.git}"

tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT

filter() {
  # Solo ramas y etiquetas; se ignoran las referencias "peeled" (^{}).
  grep -E 'refs/(heads|tags)/' "$1" | grep -v '\^{}' | sort -k2 || true
}

printf 'Consultando %s ...\n' "$GH_REPO"
git ls-remote "$GH_REPO" > "$tmp/gh.raw"
printf 'Consultando %s ...\n' "$GL_REPO"
git ls-remote "$GL_REPO" > "$tmp/gl.raw"

filter "$tmp/gh.raw" > "$tmp/gh.txt"
filter "$tmp/gl.raw" > "$tmp/gl.txt"

printf '\n%-42s %-42s %s\n' "GITHUB" "GITLAB" "ESTADO"
printf '%-42s %-42s %s\n' "------------------------------------------" "------------------------------------------" "--------"
while IFS=$'\t' read -r sha ref; do
  [ -z "${sha:-}" ] && continue
  other="$(awk -v r="$ref" '$2 == r {print $1}' "$tmp/gl.txt")"
  if [ "$other" = "$sha" ]; then
    estado="OK"
  else
    estado="DIFERENTE (${other:-ausente})"
  fi
  printf '%-42s %-42s %s\n' "${sha:0:40} $ref" "${other:0:40} ${ref}" "$estado"
done < "$tmp/gh.txt"

extras="$(awk 'NR==FNR {a[$2]=1; next} !($2 in a) {print $2}' "$tmp/gh.txt" "$tmp/gl.txt")"
if [ -n "$extras" ]; then
  printf '\nReferencias solo en GitLab:\n%s\n' "$extras"
fi

if diff -q "$tmp/gh.txt" "$tmp/gl.txt" >/dev/null 2>&1 && [ -z "$extras" ]; then
  printf '\nRESULTADO: espejos sincronizados correctamente.\n'
  exit 0
fi

printf '\nRESULTADO: los espejos NO estan sincronizados.\n'
exit 1
