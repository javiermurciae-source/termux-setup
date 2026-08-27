#!/data/data/com.termux/files/usr/bin/bash

set -euo pipefail

PROGRAM="${0##*/}"

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

usage() {
    cat <<'EOF'
Document Lab CLI para Termux

Uso:
  doclab check
  doclab info ARCHIVO.pdf
  doclab text ARCHIVO.pdf [SALIDA.txt|-]
  doclab preview ARCHIVO.pdf [PAGINA]
  doclab select ENTRADA.pdf PAGINAS SALIDA.pdf
  doclab split ENTRADA.pdf DIRECTORIO
  doclab merge SALIDA.pdf ENTRADA1.pdf ENTRADA2.pdf [...]
  doclab optimize ENTRADA.pdf SALIDA.pdf [screen|ebook|printer|prepress]
  doclab image ENTRADA.jpg SALIDA.jpg
  doclab svg ENTRADA.svg SALIDA.pdf
  doclab typst ENTRADA.typ SALIDA.pdf
  doclab latex ENTRADA.tex [DIRECTORIO_SALIDA]
  doclab markdown ENTRADA.md SALIDA.pdf
  doclab ocr ENTRADA.png SALIDA.pdf [IDIOMA]
  doclab metadata ARCHIVO

Ejemplos:
  doclab select completo.pdf 1-2 recortado.pdf
  doclab merge unido.pdf portada.pdf contenido.pdf
  doclab typst hoja-vida.typ hoja-vida.pdf
  doclab ocr escaneo.jpg escaneo-buscable.pdf spa

Por seguridad no se sobrescriben archivos. Para permitirlo:
  DOCLAB_FORCE=1 doclab ...
EOF
}

need_command() {
    command -v "$1" >/dev/null 2>&1 || die "falta el comando '$1'"
}

need_file() {
    [ -f "$1" ] || die "no existe el archivo: $1"
}

prepare_output() {
    local output="$1"
    if [ -e "$output" ] && [ "${DOCLAB_FORCE:-0}" != "1" ]; then
        die "la salida ya existe: $output (usa DOCLAB_FORCE=1 para reemplazarla)"
    fi
    mkdir -p "$(dirname "$output")"
}

check_tools() {
    local failed=0
    local command_name
    local commands=(
        typst tectonic pandoc pdfinfo pdftotext pdffonts pdfimages
        pdftoppm pdfseparate pdfunite qpdf gs magick rsvg-convert
        file fc-match exiftool tesseract unpaper chafa
    )

    for command_name in "${commands[@]}"; do
        if command -v "$command_name" >/dev/null 2>&1; then
            printf 'OK     %-18s %s\n' "$command_name" "$(command -v "$command_name")"
        else
            printf 'FALTA  %s\n' "$command_name"
            failed=1
        fi
    done

    printf '\nIdiomas OCR:\n'
    tesseract --list-langs 2>/dev/null || true
    return "$failed"
}

[ "$#" -gt 0 ] || {
    usage
    exit 1
}

action="$1"
shift

case "$action" in
    help|-h|--help)
        usage
        ;;

    check)
        check_tools
        ;;

    info)
        [ "$#" -eq 1 ] || die "uso: $PROGRAM info ARCHIVO.pdf"
        need_command pdfinfo
        need_file "$1"
        pdfinfo "$1"
        printf '\nTipografías:\n'
        pdffonts "$1"
        ;;

    text)
        [ "$#" -ge 1 ] && [ "$#" -le 2 ] || die "uso: $PROGRAM text ARCHIVO.pdf [SALIDA.txt|-]"
        need_command pdftotext
        need_file "$1"
        output="${2:--}"
        if [ "$output" = "-" ]; then
            pdftotext -layout "$1" -
        else
            prepare_output "$output"
            pdftotext -layout "$1" "$output"
            printf 'Texto guardado en: %s\n' "$output"
        fi
        ;;

    preview)
        [ "$#" -ge 1 ] && [ "$#" -le 2 ] || die "uso: $PROGRAM preview ARCHIVO.pdf [PAGINA]"
        need_command pdftoppm
        need_command chafa
        need_file "$1"
        page="${2:-1}"
        [[ "$page" =~ ^[1-9][0-9]*$ ]] || die "la página debe ser un entero positivo"
        preview_dir="$(mktemp -d)"
        trap 'rm -rf "$preview_dir"' EXIT
        pdftoppm -f "$page" -l "$page" -singlefile -png -r 110 "$1" "$preview_dir/page" >/dev/null 2>&1
        chafa "$preview_dir/page.png"
        ;;

    select)
        [ "$#" -eq 3 ] || die "uso: $PROGRAM select ENTRADA.pdf PAGINAS SALIDA.pdf"
        need_command qpdf
        need_file "$1"
        prepare_output "$3"
        qpdf --empty --pages "$1" "$2" -- "$3"
        printf 'PDF creado en: %s\n' "$3"
        ;;

    split)
        [ "$#" -eq 2 ] || die "uso: $PROGRAM split ENTRADA.pdf DIRECTORIO"
        need_command pdfseparate
        need_file "$1"
        if [ -d "$2" ] && [ -n "$(find "$2" -mindepth 1 -maxdepth 1 -print -quit 2>/dev/null)" ] && [ "${DOCLAB_FORCE:-0}" != "1" ]; then
            die "el directorio no está vacío: $2"
        fi
        mkdir -p "$2"
        pdfseparate "$1" "$2/page-%d.pdf"
        printf 'Páginas guardadas en: %s\n' "$2"
        ;;

    merge)
        [ "$#" -ge 3 ] || die "uso: $PROGRAM merge SALIDA.pdf ENTRADA1.pdf ENTRADA2.pdf [...]"
        need_command pdfunite
        output="$1"
        shift
        prepare_output "$output"
        for input in "$@"; do need_file "$input"; done
        pdfunite "$@" "$output"
        printf 'PDF unido en: %s\n' "$output"
        ;;

    optimize)
        [ "$#" -ge 2 ] && [ "$#" -le 3 ] || die "uso: $PROGRAM optimize ENTRADA.pdf SALIDA.pdf [screen|ebook|printer|prepress]"
        need_command gs
        need_file "$1"
        prepare_output "$2"
        quality="${3:-ebook}"
        case "$quality" in screen|ebook|printer|prepress) ;; *) die "calidad no válida: $quality" ;; esac
        gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.7 -dPDFSETTINGS="/$quality" \
            -dNOPAUSE -dQUIET -dBATCH -sOutputFile="$2" "$1"
        printf 'PDF optimizado en: %s\n' "$2"
        ;;

    image)
        [ "$#" -eq 2 ] || die "uso: $PROGRAM image ENTRADA.jpg SALIDA.jpg"
        need_command magick
        need_file "$1"
        prepare_output "$2"
        magick "$1" -auto-orient -resize '1600x1600>' -strip -quality 88 "$2"
        printf 'Imagen preparada en: %s\n' "$2"
        ;;

    svg)
        [ "$#" -eq 2 ] || die "uso: $PROGRAM svg ENTRADA.svg SALIDA.pdf"
        need_command rsvg-convert
        need_file "$1"
        prepare_output "$2"
        rsvg-convert -f pdf -o "$2" "$1"
        printf 'PDF creado en: %s\n' "$2"
        ;;

    typst)
        [ "$#" -eq 2 ] || die "uso: $PROGRAM typst ENTRADA.typ SALIDA.pdf"
        need_command typst
        need_file "$1"
        prepare_output "$2"
        typst compile "$1" "$2"
        printf 'PDF creado en: %s\n' "$2"
        ;;

    latex)
        [ "$#" -ge 1 ] && [ "$#" -le 2 ] || die "uso: $PROGRAM latex ENTRADA.tex [DIRECTORIO_SALIDA]"
        need_command tectonic
        need_file "$1"
        output_dir="${2:-$(dirname "$1")}"
        mkdir -p "$output_dir"
        tectonic -o "$output_dir" "$1"
        printf 'Salida LaTeX guardada en: %s\n' "$output_dir"
        ;;

    markdown)
        [ "$#" -eq 2 ] || die "uso: $PROGRAM markdown ENTRADA.md SALIDA.pdf"
        need_command pandoc
        need_file "$1"
        prepare_output "$2"
        pandoc "$1" --pdf-engine=tectonic -o "$2"
        printf 'PDF creado en: %s\n' "$2"
        ;;

    ocr)
        [ "$#" -ge 2 ] && [ "$#" -le 3 ] || die "uso: $PROGRAM ocr ENTRADA.png SALIDA.pdf [IDIOMA]"
        need_command tesseract
        need_file "$1"
        output="$2"
        language="${3:-spa}"
        case "$output" in *.pdf) ;; *) die "la salida debe terminar en .pdf" ;; esac
        prepare_output "$output"
        tesseract "$1" "${output%.pdf}" -l "$language" pdf
        printf 'PDF con OCR creado en: %s\n' "$output"
        ;;

    metadata)
        [ "$#" -eq 1 ] || die "uso: $PROGRAM metadata ARCHIVO"
        need_command exiftool
        need_file "$1"
        exiftool "$1"
        ;;

    *)
        usage >&2
        die "acción desconocida: $action"
        ;;
esac
