#!/data/data/com.termux/files/usr/bin/bash
#
# Verificador de códigos - JP Streaming (via curl)
#

URL_BASE="https://jp-streaming.pages.dev/api/codes"
ROJO='\033[0;31m'
VERDE='\033[0;32m'
AMARILLO='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

servicio=""
correo=""

preguntar_servicio() {
    echo -e "${CYAN}=== Verificador de Códigos JP Streaming ===${NC}"
    echo ""
    echo "  1) Netflix"
    echo "  2) Disney+"
    echo ""
    read -rp "Selecciona el servicio [1-2]: " opcion
    case "$opcion" in
        1) servicio="netflix" ;;
        2) servicio="disney_plus" ;;
        *) echo -e "${ROJO}Opción inválida.${NC}"; preguntar_servicio ;;
    esac
}

preguntar_correo() {
    read -rp "Correo electrónico: " correo
    if ! [[ "$correo" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        echo -e "${ROJO}Correo no válido, inténtalo de nuevo.${NC}"
        preguntar_correo
    fi
}

verificar() {
    local url="${URL_BASE}/${servicio}/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$correo" 2>/dev/null || echo "$correo")"
    echo ""
    echo -e "${AMARILLO}Consultando código para ${correo} (${servicio})...${NC}"

    respuesta=$(curl -s --max-time 20 "$url")
    code_http=$(curl -s -o /dev/null -w '%{http_code}' --max-time 20 "$url")

    echo ""
    echo -e "${CYAN}--- Respuesta (HTTP $code_http) ---${NC}"

    if command -v jq >/dev/null 2>&1; then
        servicio_resp=$(echo "$respuesta" | jq -r '.service // empty')
        tipo=$(echo "$respuesta" | jq -r '.type // empty')
        valor=$(echo "$respuesta" | jq -r '.value // empty')
        mensaje=$(echo "$respuesta" | jq -r '.message // empty')

        [ -n "$servicio_resp" ] && echo "  Servicio : $servicio_resp"
        [ -n "$tipo" ] && echo "  Tipo     : $tipo"
        [ -n "$valor" ] && echo "  Valor    : $valor"
        [ -n "$mensaje" ] && echo "  Mensaje  : $mensaje"

        if [[ "$mensaje" == *"éxito"* ]]; then
            echo ""
            echo -e "${VERDE}[✓] Código encontrado${NC}"
            if [ -t 1 ]; then
                printf '%s' "$valor" | termux-clipboard-set 2>/dev/null \
                    && echo -e "${VERDE}Copiado al portapapeles.${NC}"
            fi
        else
            echo ""
            echo -e "${ROJO}[✗] Sin código aún (espera unos minutos y reintenta)${NC}"
        fi
    else
        echo "$respuesta"
    fi
}

# Modo directo (sin menús):
#   codc correo@x.com        -> Netflix
#   codc n correo@x.com      -> Netflix
#   codc d correo@x.com      -> Disney+
if [[ $# -ge 1 ]]; then
    servicio="netflix"
    case "$1" in
        n|netflix)          servicio="netflix";     correo="${2:-}" ;;
        d|disney|disney_plus) servicio="disney_plus"; correo="${2:-}" ;;
        *)                  correo="$1" ;;
    esac
    if ! [[ "$correo" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        echo -e "${ROJO}Uso: codc [n|d] <correo>${NC}" >&2
        exit 1
    fi
    verificar
    exit 0
fi

while true; do
    clear
    preguntar_servicio
    preguntar_correo
    verificar
    echo ""
    read -rp "¿Verificar otro? [s/N]: " de_nuevo
    [[ "$de_nuevo" =~ ^[sS]$ ]] || break
done
echo -e "${CYAN}¡Listo!${NC}"
