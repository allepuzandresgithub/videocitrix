#/bin/bash
set -euo pipefail
SRC="${1:-../yt-music-server}"                       # origen (puedes pasar otro como primer argumento)
BACKUP_DIR="${2:-../yt-music-server_backup}"         # carpeta de backups (puedes pasar otro como segundo argumento)
FORCED_INDEX="${3:-}"                               # si pasas un índice como tercer argumento, se usa
# Comprobar origen
if [ ! -e "$SRC" ]; then
  echo "Error: origen no encontrado: $SRC" >&2
  exit 2
fi

# Crear carpeta de backup si no existe
mkdir -p "$BACKUP_DIR"

# Si se fuerza un índice válido, úsalo
if [ -n "$FORCED_INDEX" ]; then
  if [[ ! "$FORCED_INDEX" =~ ^[0-9]+$ ]]; then
    echo "Error: índice forzado no es numérico: $FORCED_INDEX" >&2
    exit 3
  fi
  NEXT_NUM=$((10#$FORCED_INDEX))
else
  # Buscar el mayor índice existente y sumar 1
  MAX=0
  shopt -s nullglob
  for d in "$BACKUP_DIR"/yt-music-server_copy*; do
    base="${d##*/}"                     # extrae nombre del directorio
    num="${base##*_copy}"               # extrae la parte numérica
    if [[ "$num" =~ ^[0-9]+$ ]]; then
      n=$((10#$num))
      (( n > MAX )) && MAX=$n
    fi
  done
  shopt -u nullglob
  NEXT_NUM=$((MAX + 1))
fi

# Formatear con dos dígitos (cambia %02d si quieres más dígitos)
LABEL=$(printf "%02d" "$NEXT_NUM")
DEST="$BACKUP_DIR/yt-music-server_copy${LABEL}"

# Ejecutar copia (preserva atributos; -v para ver progreso)
cp -a -v "$SRC" "$DEST"

echo "Backup creado en: $DEST"



