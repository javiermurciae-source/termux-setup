#!/data/data/com.termux/files/usr/bin/bash
# ════════════════════════════════════════════════════════════════
# 🔐 VERIFICADOR DE CÓDIGOS & OTP - JP STREAMING (ULTRA MODERNO)
# ════════════════════════════════════════════════════════════════

URL_BASE="https://jp-streaming.pages.dev/api/codes"

C_CYAN="\033[1;36m"
C_BLUE="\033[1;34m"
C_GREEN="\033[1;32m"
C_YELLOW="\033[1;33m"
C_MAGENTA="\033[1;35m"
C_RED="\033[1;31m"
C_WHITE="\033[1;37m"
C_DIM="\033[2;37m"
C_BOLD="\033[1m"
C_RESET="\033[0m"

servicio=""
correo=""
nombre_servicio=""

banner() {
    clear
    echo -e "${C_CYAN}╭──────────────────────────────────────────────────────────────╮${C_RESET}"
    echo -e "${C_CYAN}│     🔐  VERIFICADOR DE CÓDIGOS OTP - JP STREAMING ⚡         │${C_RESET}"
    echo -e "${C_CYAN}╰──────────────────────────────────────────────────────────────╯${C_RESET}\n"
}

preguntar_servicio() {
    echo -e "${C_YELLOW}Selecciona la plataforma de streaming:${C_RESET}\n"
    echo -e "  ${C_CYAN}[1]${C_RESET} ${C_BOLD}🎬 Netflix${C_RESET}"
    echo -e "  ${C_CYAN}[2]${C_RESET} ${C_BOLD}✨ Disney+${C_RESET}\n"
    
    echo -ne "${C_GREEN}👉 Opción [1-2, defecto: 1 (Netflix)]: ${C_RESET}"
    read -r opcion
    case "$opcion" in
        2) servicio="disney_plus"; nombre_servicio="Disney+" ;;
        *) servicio="netflix";     nombre_servicio="Netflix" ;;
    esac
}

preguntar_correo() {
    echo ""
    while true; do
        echo -ne "${C_WHITE}✉️  Ingresa el correo electrónico: ${C_RESET}"
        read -r correo
        if [[ "$correo" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
            break
        fi
        echo -e "${C_RED}❌ Correo no válido. Inténtalo de nuevo.${C_RESET}"
    done
}

verificar() {
    local url="${URL_BASE}/${servicio}/$(python3 -c "import urllib.parse,sys;print(urllib.parse.quote(sys.argv[1],safe=''))" "$correo" 2>/dev/null || echo "$correo")"
    
    echo -e "\n${C_BLUE}⏳ Consultando código OTP para ${C_WHITE}${correo}${C_BLUE} en ${C_YELLOW}${nombre_servicio}${C_BLUE}...${C_RESET}"
    
    respuesta=$(curl -s --max-time 15 "$url")
    code_http=$(curl -s -o /dev/null -w '%{http_code}' --max-time 15 "$url")

    echo ""
    if command -v jq >/dev/null 2>&1; then
        servicio_resp=$(echo "$respuesta" | jq -r '.service // empty' 2>/dev/null)
        tipo=$(echo "$respuesta" | jq -r '.type // empty' 2>/dev/null)
        valor=$(echo "$respuesta" | jq -r '.value // empty' 2>/dev/null)
        mensaje=$(echo "$respuesta" | jq -r '.message // empty' 2>/dev/null)

        [ -z "$servicio_resp" ] && servicio_resp="$nombre_servicio"

        echo -e "${C_CYAN}┌─────────────────────────────────────────────────────────────┐${C_RESET}"
        echo -e "${C_CYAN}│${C_RESET} ${C_YELLOW}📺 Servicio:${C_RESET}   ${C_WHITE}${servicio_resp}${C_RESET}"
        [ -n "$tipo" ] && echo -e "${C_CYAN}│${C_RESET} ${C_BLUE}🏷️  Tipo:${C_RESET}       ${C_WHITE}${tipo}${C_RESET}"
        echo -e "${C_CYAN}│${C_RESET} ${C_DIM}📧 Cuenta:${C_RESET}     ${C_DIM}${correo}${C_RESET}"
        
        if [ -n "$valor" ] && [ "$valor" != "null" ]; then
            echo -e "${C_CYAN}├─────────────────────────────────────────────────────────────┤${C_RESET}"
            echo -e "${C_CYAN}│${C_RESET} ${C_GREEN}🔑 CÓDIGO:${C_RESET}     ${C_BOLD}${C_GREEN}${valor}${C_RESET}"
            echo -e "${C_CYAN}└─────────────────────────────────────────────────────────────┘${C_RESET}"
            
            # Copiar al portapapeles de Termux automáticamente
            if command -v termux-clipboard-set >/dev/null 2>&1; then
                printf '%s' "$valor" | termux-clipboard-set 2>/dev/null
                echo -e "\n${C_GREEN}📋 ¡Código copiado automáticamente al portapapeles!${C_RESET}"
            fi
        else
            echo -e "${C_CYAN}├─────────────────────────────────────────────────────────────┤${C_RESET}"
            echo -e "${C_CYAN}│${C_RESET} ${C_RED}⚠️  Estado:${C_RESET}     ${C_RED}${mensaje:-Sin código recibido aún}${C_RESET}"
            echo -e "${C_CYAN}└─────────────────────────────────────────────────────────────┘${C_RESET}"
            echo -e "\n${C_YELLOW}💡 Tip: Si acabas de pedir el código, espera 5-10 segundos y reconsulta.${C_RESET}"
        fi
    else
        echo -e "${C_WHITE}${respuesta}${C_RESET}"
    fi
}

menu_reconsultar() {
    while true; do
        echo -e "\n${C_MAGENTA}¿Qué deseas hacer a continuación?${C_RESET}"
        echo -e "  ${C_CYAN}[1]${C_RESET} ${C_BOLD}🔄 Reconsultar este mismo correo (${correo})${C_RESET}"
        echo -e "  ${C_CYAN}[2]${C_RESET} ${C_BOLD}📧 Consultar otro correo nuevo${C_RESET}"
        echo -e "  ${C_CYAN}[3]${C_RESET} ${C_BOLD}🚪 Salir${C_RESET}\n"
        
        echo -ne "${C_GREEN}👉 Selecciona una opción [1-3, defecto: 1]: ${C_RESET}"
        read -r accion
        
        case "$accion" in
            2)
                return 1 # Otro correo
                ;;
            3|"q"|"salir"|"exit")
                echo -e "\n${C_CYAN}👋 ¡Hasta luego!${C_RESET}\n"
                exit 0
                ;;
            *)
                echo -e "\n${C_YELLOW}🔄 Reconsultando código para ${correo}...${C_RESET}"
                verificar
                ;;
        esac
    done
}

# ── Modo CLI Directo: codc correo@ejemplo.com o codc d correo@ejemplo.com ──
if [[ $# -ge 1 ]]; then
    servicio="netflix"
    nombre_servicio="Netflix"
    case "$1" in
        n|netflix)            servicio="netflix";     nombre_servicio="Netflix"; correo="${2:-}" ;;
        d|disney|disney_plus) servicio="disney_plus"; nombre_servicio="Disney+"; correo="${2:-}" ;;
        *)                    correo="$1" ;;
    esac
    
    if ! [[ "$correo" =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        echo -e "${C_RED}Uso rápido: codc [n|d] <correo>${C_RESET}" >&2
        exit 1
    fi
    
    banner
    verificar
    menu_reconsultar
    exit 0
fi

# ── Modo Interactivo Principal ──
while true; do
    banner
    preguntar_servicio
    preguntar_correo
    verificar
    menu_reconsultar
done
