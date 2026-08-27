# Document Lab CLI

Entorno de creación, análisis, conversión, OCR y mantenimiento de documentos
desde Termux, sin interfaz gráfica ni Chromium.

## Herramientas

- **Typst:** motor principal para hojas de vida, informes y documentos modernos.
- **Tectonic:** motor LaTeX reproducible para documentos técnicos y académicos.
- **Pandoc:** conversión desde Markdown y otros formatos.
- **Poppler:** inspección, texto, fuentes, imágenes y renderizado de PDF.
- **QPDF:** selección, reorganización y validación estructural de páginas.
- **Ghostscript:** optimización y compatibilidad de PDF/PostScript.
- **ImageMagick, Librsvg y Pillow:** preparación de fotografías, imágenes y SVG.
- **Tesseract y Unpaper:** OCR y preparación de escaneos.
- **ExifTool y Fontconfig:** metadatos y diagnóstico de tipografías.
- **Chafa:** previsualización de páginas directamente en la terminal.

## Comando unificado

El instalador publica `doclab` en `$PREFIX/bin`.

```bash
doclab check
doclab info documento.pdf
doclab preview documento.pdf 1
doclab select completo.pdf 1-2 recortado.pdf
doclab merge unido.pdf portada.pdf contenido.pdf
doclab optimize grande.pdf reducido.pdf ebook
doclab typst hoja-vida.typ hoja-vida.pdf
doclab latex informe.tex ./salida
doclab markdown informe.md informe.pdf
doclab ocr escaneo.jpg escaneo-buscable.pdf spa
```

Por defecto, `doclab` no sobrescribe archivos existentes. Para autorizar una
sobrescritura explícita:

```bash
DOCLAB_FORCE=1 doclab optimize entrada.pdf salida.pdf ebook
```

## OCR en español

El setup instala `spa.traineddata` desde el repositorio oficial
`tesseract-ocr/tessdata_fast`, fijado en la versión `4.1.0` y validado con
SHA-256 antes de copiarlo al directorio de Tesseract.
