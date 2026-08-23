#!/data/data/com.termux/files/usr/bin/bash

DOWNLOADS_DIR="$HOME/storage/downloads"
FASTFETCH_GIF="$HOME/.config/fastfetch/descargas.gif"

cd "$DOWNLOADS_DIR" || { echo "No se pudo acceder a $DOWNLOADS_DIR"; exit 1; }

mapfile -d '' GIFS < <(find . -maxdepth 1 -name '*.gif' -print0 | sort -z)
if [ ${#GIFS[@]} -eq 0 ]; then
    echo "No hay GIFs en $DOWNLOADS_DIR"
    exit 1
fi

echo "GIFs disponibles en $DOWNLOADS_DIR:"
echo "-----------------------------------"
for i in "${!GIFS[@]}"; do
    FILE="${GIFS[i]#./}"
    SIZE=$(du -h "$FILE" 2>/dev/null | cut -f1)
    echo "  $((i+1))) $FILE (${SIZE:-?})"
done
echo "  0) Salir"
echo "-----------------------------------"

read -p "Selecciona un número: " choice

if [[ "$choice" == "0" ]]; then
    echo "Cancelado"
    exit 0
fi

if ! [[ "$choice" =~ ^[0-9]+$ ]] || [ "$choice" -lt 1 ] || [ "$choice" -gt ${#GIFS[@]} ]; then
    echo "Opción inválida"
    exit 1
fi

SELECTED="${GIFS[$((choice-1))]#./}"
cp "$SELECTED" "$FASTFETCH_GIF"
echo "Copiado: $SELECTED -> $FASTFETCH_GIF"
echo "Limpiando cache..."
rm -rf ~/.cache/fastfetch 2>/dev/null
echo "Ejecutando fastfetch..."
fastfetch