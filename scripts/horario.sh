#!/data/data/com.termux/files/usr/bin/bash
# ════════════════════════════════════════════════════════════════
# 🎓 HORARIO UNIVERSITARIO PRO - INGENIERÍA DE SISTEMAS
# ════════════════════════════════════════════════════════════════
: "${LANG:=C.UTF-8}"; : "${LC_ALL:=C.UTF-8}"; export LANG LC_ALL

# Paleta de Colores ANSI Moderna
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

HOY=$(date +%u)                                # 1=Lun ... 7=Dom
AHORA=$(( $(date +%H) * 60 + $(date +%M) ))    # minutos desde medianoche
FECHA_ACTUAL=$(date +"%d de %B de %Y")
DIAS=("" "Lunes" "Martes" "Miércoles" "Jueves" "Viernes" "Sábado" "Domingo")

# día|inicio_min|fin_min|hora_txt|icono|asignatura|aula
CLASES=(
  "2|480|720|08:00 - 12:00|📡|Comunicación de Datos|Presencial"
  "4|480|720|08:00 - 12:00|📈|Investigación de Operaciones 1|Presencial"
  "4|1080|1260|18:00 - 21:00|💻|Ingeniería de Software|Presencial"
  "5|1080|1260|18:00 - 21:00|📊|Electiva Prof. 2 (Power BI)|Virtual / Lab"
  "6|420|600|07:00 - 10:00|🛡️|Seguridad Informática|Presencial"
)

fmt_min() { printf '%02d:%02d' $(($1/60)) $(($1%60)); }

fmt_delta() {
    local t=$1 dd hh mm o=""
    dd=$((t/1440)); hh=$((t%1440/60)); mm=$((t%60))
    (( dd )) && o+="${dd}d "
    (( hh || dd )) && o+="${hh}h "
    printf '%s%d min' "$o" "$mm"
}

banner() {
    echo -e "${C_CYAN}╭────────────────────────────────────────────────────────────────────────────╮${C_RESET}"
    echo -e "${C_CYAN}│  🎓  HORARIO ACADÉMICO · INGENIERÍA DE SISTEMAS ($(date +%Y))            ⚡  │${C_RESET}"
    echo -e "${C_CYAN}│  📅  Hoy es ${C_YELLOW}${DIAS[$HOY]}${C_CYAN}, ${FECHA_ACTUAL}                           │${C_RESET}"
    echo -e "${C_CYAN}╰────────────────────────────────────────────────────────────────────────────╯${C_RESET}\n"
}

mostrar_horario() {
    echo -e "${C_CYAN}┌─────────────┬─────────────────┬────────────────────────────────────────────┐${C_RESET}"
    echo -e "${C_CYAN}│${C_RESET} ${C_BOLD}🗓️  DÍA${C_RESET}     ${C_CYAN}│${C_RESET} ${C_BOLD}⏰ HORARIO${C_RESET}       ${C_CYAN}│${C_RESET} ${C_BOLD}📚 ASIGNATURA / MATERIA${C_RESET}                      ${C_CYAN}│${C_RESET}"
    echo -e "${C_CYAN}├─────────────┼─────────────────┼────────────────────────────────────────────┤${C_RESET}"

    for row in "${CLASES[@]}"; do
        IFS='|' read -r d ini fin htxt icon asig aula <<< "$row"
        dtxt="${DIAS[$d]}"
        
        # Formatear si es la clase de hoy o si está en curso ahora
        if (( d == HOY && AHORA >= ini && AHORA < fin )); then
            # EN CLASE AHORA MISMO
            printf "${C_CYAN}│${C_RESET} ${C_BOLD}${C_GREEN}🟢 %-8s${C_RESET} ${C_CYAN}│${C_RESET} ${C_BOLD}${C_GREEN}%-15s${C_RESET} ${C_CYAN}│${C_RESET} ${C_BOLD}${C_GREEN}%s %-32s (EN VIVO)${C_RESET} ${C_CYAN}│${C_RESET}\n" "$dtxt" "$htxt" "$icon" "$asig"
        elif (( d == HOY )); then
            # ES HOY
            printf "${C_CYAN}│${C_RESET} ${C_BOLD}${C_YELLOW}⭐ %-8s${C_RESET} ${C_CYAN}│${C_RESET} ${C_YELLOW}%-15s${C_RESET} ${C_CYAN}│${C_RESET} ${C_WHITE}%s %-38s${C_RESET} ${C_CYAN}│${C_RESET}\n" "$dtxt" "$htxt" "$icon" "$asig"
        else
            # OTROS DÍAS
            printf "${C_CYAN}│${C_RESET} ${C_WHITE}%-11s${C_RESET} ${C_CYAN}│${C_RESET} ${C_DIM}%-15s${C_RESET} ${C_CYAN}│${C_RESET} ${C_WHITE}%s %-38s${C_RESET} ${C_CYAN}│${C_RESET}\n" "$dtxt" "$htxt" "$icon" "$asig"
        fi
    done
    echo -e "${C_CYAN}└─────────────┴─────────────────┴────────────────────────────────────────────┘${C_RESET}"
}

estado_actual() {
    local best=2147483647 bi=-1 bd=0 bini=0 ec=-1 efin=0 i row d ini fin icon asig aula
    for i in "${!CLASES[@]}"; do
        IFS='|' read -r d ini fin _ icon asig aula <<< "${CLASES[$i]}"
        if (( d == HOY )); then
            if (( AHORA >= ini && AHORA < fin )); then 
                ec=$i; efin=$fin
            fi
            (( AHORA >= ini )) && continue
        elif (( d < HOY )); then
            continue
        fi
        local delta=$(( (d - HOY) * 1440 + ini - AHORA ))
        (( delta < best )) && { best=$delta; bd=$d; bi=$i; }
    done

    echo ""
    echo -e "${C_MAGENTA}📌 ESTADO ACADÉMICO ACTUAL:${C_RESET}"
    if (( ec >= 0 )); then
        IFS='|' read -r _ _ _ htxt icon asig aula <<< "${CLASES[$ec]}"
        echo -e "  ${C_GREEN}🟢 ¡ESTÁS EN CLASE AHORA MISMO!${C_RESET}"
        echo -e "     ${C_BOLD}${icon}  ${asig}${C_RESET} ${C_DIM}(Termina a las $(fmt_min $efin))${C_RESET}\n"
    elif (( bi >= 0 )); then
        IFS='|' read -r _ _ _ htxt icon asig aula <<< "${CLASES[$bi]}"
        echo -e "  ${C_YELLOW}⏳ Siguiente clase:${C_RESET} ${C_BOLD}${icon} ${asig}${C_RESET}"
        echo -e "     🗓️  ${C_WHITE}${DIAS[$bd]}${C_RESET} a las ${C_YELLOW}${htxt}${C_RESET} ${C_DIM}(Faltan: ${C_CYAN}$(fmt_delta $best)${C_DIM})${C_RESET}\n"
    else
        echo -e "  ${C_CYAN}🎉 ¡Sin más clases esta semana! Modo descanso / hacking activado.${C_RESET}\n"
    fi
}

banner
mostrar_horario
estado_actual
