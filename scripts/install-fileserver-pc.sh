#!/bin/bash
# FileServer para PC (Linux/Mac)
# Instala y ejecuta el servidor de archivos

set -e

INSTALL_DIR="$HOME/.local/share/fileserver"
SCRIPT_URL="https://raw.githubusercontent.com/javiermurciae-source/termux-setup/main/scripts/fileserver.py"

echo "📁 FileServer - Instalador para PC"
echo "=================================="

# Crear directorio
mkdir -p "$INSTALL_DIR"

# Descargar script
echo "⬇️ Descargando FileServer..."
curl -sL "$SCRIPT_URL" -o "$INSTALL_DIR/fileserver.py"

if [ ! -f "$INSTALL_DIR/fileserver.py" ]; then
    echo "❌ Error al descargar FileServer"
    exit 1
fi

chmod +x "$INSTALL_DIR/fileserver.py"

# Crear script de inicio
cat > "$HOME/.local/bin/fileserver" << 'LAUNCHER'
#!/bin/bash
python3 "$HOME/.local/share/fileserver/fileserver.py" "$@"
LAUNCHER
chmod +x "$HOME/.local/bin/fileserver"

# Verificar python3
if ! command -v python3 &>/dev/null; then
    echo "⚠️ Python3 no encontrado. Instalando..."
    if command -v pacman &>/dev/null; then
        sudo pacman -S --noconfirm python
    elif command -v apt &>/dev/null; then
        sudo apt install -y python3
    elif command -v dnf &>/dev/null; then
        sudo dnf install -y python3
    fi
fi

echo ""
echo "✅ FileServer instalado!"
echo ""
echo "📋 Uso:"
echo "  fileserver                    # Sirve ~/"
echo "  fileserver /ruta/carpeta      # Sirve esa carpeta"
echo "  fileserver --port 9090        # Puerto personalizado"
echo ""
echo "🌐 Desde tu teléfono:"
echo "  http://tailscale-termux.ts.net:8080"
echo ""
