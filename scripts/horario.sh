#!/data/data/com.termux/files/usr/bin/bash
# ── Horario universitario bonito para la terminal ──
: "${LANG:=C.UTF-8}"; : "${LC_ALL:=C.UTF-8}"; export LANG LC_ALL

R=$'\e[0m'; B=$'\e[1m'; DIM=$'\e[2m'
CY=$'\e[96m'; GR=$'\e[92m'; YE=$'\e[93m'; MA=$'\e[95m'

HOY=$(date +%u)                                # 1=Lun ... 7=Dom
AHORA=$(( $(date +%H) * 60 + $(date +%M) ))    # minutos desde medianoche
DIAS=("" "Lunes" "Martes" "Miércoles" "Jueves" "Viernes" "Sábado" "Domingo")

# día|inicio_min|fin_min|hora_txt|asignatura
CLASES=(
  "2|480|720|08:00-12:00|Comunicación de datos"
  "4|480|720|08:00-12:00|Investigación de operaciones 1"
  "4|1080|1260|18:00-21:00|Ingeniería de software"
  "5|1080|1260|18:00-21:00|Electiva Profesional 2 (Power BI)"
  "6|420|600|07:00-10:00|Electiva complementaria (Seguridad Informática)"
)

rep()  { local o="" i; for ((i=0;i<$2;i++)); do o+="$1"; done; printf '%s' "$o"; }
pad()  { local s="$1"; while (( ${#s} < $2 )); do s+=" "; done; printf '%s' "$s"; }
cbox() { local gap=$(( $2 - ${#1} )) l=$(( gap / 2 )); pad "" "$l"; printf '%s' "$1"; pad "" $(( gap - l )); }
fmt_min()  { printf '%02d:%02d' $(($1/60)) $(($1%60)); }
fmt_delta(){ local t=$1 o="" dd hh mm
             dd=$((t/1440)); hh=$((t%1440/60)); mm=$((t%60))
             (( dd )) && o+="${dd}d "; (( hh || dd )) && o+="${hh}h "; printf '%s%d min' "$o" "$mm"; }

CD=11; CH=14; CA=49
WI=$(( CD + CH + CA + 2 ))
TOP="╔$(rep '═' $CD)╦$(rep '═' $CH)╦$(rep '═' $CA)╗"
SEP="╠$(rep '═' $CD)╬$(rep '═' $CH)╬$(rep '═' $CA)╣"
BOT="╚$(rep '═' $CD)╩$(rep '═' $CH)╩$(rep '═' $CA)╝"

tabla() {
  bline() { printf '%s║%s%s%s║%s\n' "${B}${CY}" "$2" "$(cbox "$1" $WI)" "$R" "${B}${CY}"; }
  echo
  echo "${B}${CY}${TOP}${R}"
  bline "HORARIO DE CLASES · $(date +%Y)" "${B}${CY}"
  bline "Ingeniería de Sistemas" "${B}"
  echo "${B}${CY}${SEP}${R}"
  printf '%s║%s║%s║%s║%s\n' "${B}${CY}" "$(cbox "DÍA" $CD)" "$(cbox "HORA" $CH)" "$(cbox "ASIGNATURA" $CA)" "$R"
  echo "${B}${CY}${SEP}${R}"
  local pd=""
  for row in "${CLASES[@]}"; do
    IFS='|' read -r d ini fin htxt asig <<< "$row"
    local dtxt="${DIAS[$d]}"
    (( d == HOY )) && dtxt+=" ●"
    if (( d == HOY )); then
      printf '%s║%s║%s║%s║%s\n' "${B}${GR}" "$(cbox "$dtxt" $CD)" "$(cbox "$htxt" $CH)" "$(cbox "$asig" $CA)" "$R"
    else
      printf '%s║%s║%s║%s║%s\n' "${CY}" "${YE}$(cbox "$dtxt" $CD)${R}${CY}" "$(cbox "$htxt" $CH)" "$(cbox "$asig" $CA)" "$R"
    fi
  done
  echo "${B}${CY}${BOT}${R}"
}

compacta() {
  echo
  echo " ${B}${CY}HORARIO · Ingeniería de Sistemas${R}"
  echo " ${DIM}$(rep '─' 32)${R}"
  local pd=""
  for row in "${CLASES[@]}"; do
    IFS='|' read -r d ini fin htxt asig <<< "$row"
    if (( d != pd )); then
      pd=$d
      local col="${B}${CY}"
      (( d == HOY )) && col="${B}${GR}"
      printf '\n %s◆ %s%s\n' "$col" "${DIAS[$d]}" "$R"
    fi
    if (( d == HOY && AHORA >= ini && AHORA < fin )); then
      printf '   %s▸ %s · %s (en curso)%s\n' "${GR}${B}" "$htxt" "$asig" "$R"
    elif (( d == HOY )); then
      printf '   %s%s · %s%s\n' "${GR}" "$htxt" "$asig" "$R"
    else
      printf '   %s%s · %s%s\n' "${DIM}" "$htxt" "$asig" "$R"
    fi
  done
}

estado() {
  local best=2147483647 bi=-1 bd=0 bini=0 ec=-1 efin=0 i row d ini fin asig
  for i in "${!CLASES[@]}"; do
    IFS='|' read -r d ini fin _ asig <<< "${CLASES[$i]}"
    if (( d == HOY )); then
      if (( AHORA >= ini && AHORA < fin )); then ec=$i; efin=$fin; fi
      (( AHORA >= ini )) && continue
    elif (( d < HOY )); then
      continue
    fi
    local delta=$(( (d - HOY) * 1440 + ini - AHORA ))
    (( delta < best )) && { best=$delta; bd=$d; bi=$i; }
  done
  echo
  echo " ${MA}${B}● Hoy es ${DIAS[$HOY]} $(date +%d/%m/%Y)${R}"
  if (( ec >= 0 )); then
    IFS='|' read -r _ _ _ _ asig <<< "${CLASES[$ec]}"
    echo " ${GR}${B}▶ EN CLASE ahora:${R} ${GR}$asig${R} ${DIM}(hasta $(fmt_min $efin))${R}"
  elif (( bi >= 0 )); then
    IFS='|' read -r _ _ _ htxt asig <<< "${CLASES[$bi]}"
    echo " ${YE}${B}▶ Próxima clase:${R} ${YE}${DIAS[$bd]} $htxt · $asig${R} ${DIM}(faltan $(fmt_delta $best))${R}"
  else
    echo " ${CY}${B}✔ Sin más clases esta semana.${R} ${DIM}¡A descansar!${R}"
  fi
  echo
}

COLS=${COLUMNS:-$(tput cols 2>/dev/null)}
COLS=${COLS:-200}
if (( COLS > 0 && COLS < WI + 2 )); then
  compacta
else
  tabla
fi
estado
