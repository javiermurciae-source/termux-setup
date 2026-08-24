# 🚀 Termux Ultimate Setup & Launcher Customization 📱⚡

Script de restauración y aprovisionamiento maestro completamente automatizado, modular e idempotente para **Termux** y **Termux Launcher**.

---

## 🌟 Características Principales

### 🧠 1. Flota de Asistentes de IA (Nativos Glibc)
Integración completa con **Core-Termux** instalando y compilando asistentes de desarrollo por IA de forma nativa:
* 🤖 `opencode`
* ⚡ `kilo` (KiloCode CLI)
* 🛡️ `freebuff`
* 🚀 `agy` (Antigravity CLI)
* ⚓ `keelcode`
* 💻 `supercode`
* 📱 `mimo` (MiMoCode)
* 📜 `codex` (Codex CLI)
* 🧠 `qwen` (Qwen Code)
* 🛠️ `cline` (Cline CLI)

### 📬 2. Suite de Correo Terminal
* ⚡ **`readmail` (o `mail`):** Lector IMAP interactivo en Python con soporte para **múltiples cuentas de Gmail**, diseño de tarjetas visuales con bordes ANSI, emojis y extracción completa de mensajes.
* 🔑 **`codc` / `verificar-cod.sh`:** Extractor automatizado de códigos 2FA/OTP por IMAP.
* 📦 **`inbox` (CLI-Inbox):** Cliente completo de Gmail para terminal basado en Rich y Prompt Toolkit.

### 🕵️ 3. Reconocimiento de Red, Fuzzing & Scraping
* ⚡ **`ssh-find` (o `ssh-pc` / `findpc`):** Escáner automático de servidores SSH en la red Wi-Fi. **Encuentra la IP cambiante de tu PC al instante y te conecta con 1 solo toque** sin tener que memorizar IPs dinámicas.
* 🌐 **`netscan` (o `lan-scan`):** Escáner interactivo de red local que lista **todas las IPs conectadas al Wi-Fi, direcciones MAC, puertas de enlace (Router) y marcas/fabricantes** con tabla ANSI formateada.
* 🌐 **`netscan` (o `lan-scan`):** Escáner interactivo de red local que lista **todas las IPs conectadas al Wi-Fi, direcciones MAC, puertas de enlace (Router) y marcas/fabricantes** con tabla ANSI formateada.
* 🔍 **WhatWeb:** Escáner avanzado de tecnologías y huellas de servidores web.
* 🕸️ **Web Scraping:** Python `requests`, `beautifulsoup4` y `html2text`.
* 💣 **Fuzzing (Opcional interactivo):**
  * `ffuf`: Fuzzer web compilado directamente en Go.
  * `SecLists`: Diccionario masivo de auditoría y pentesting (~1GB).
* 🌐 **Herramientas de red:** `nmap`, `whois`, `dnsutils`.

### 📱 4. Suite Android SDK, Build-Tools & Mobile Dev (Expo / React Native)
* 🛠️ **Android SDK & Build-Tools:** `aapt`, `aapt2`, `apksigner`, `dx`, `ecj`, `android-tools` (`adb`/`fastboot`).
* 🚀 **Desarrollo Móvil Nativo con Expo & React Native:**
  * `nodejs-lts`: Entorno JavaScript/TypeScript (incluye `npm` y `npx`).
  * `eas-cli`: Herramienta CLI de Expo Application Services para compilar APKs en la nube (`eas build`).
  * **Flujo de Trabajo:**
    ```bash
    # 1. Crear proyecto
    npx create-expo-app mi-app --template
    cd mi-app

    # 2. Servidor de desarrollo en vivo (visualizar con Expo Go en Android)
    npx expo start

    # 3. Compilar APK instalable en la nube (sin quemar recursos locales)
    eas login
    EAS_NO_VCS=1 eas build --platform android --profile preview
    ```
* 🔬 **Ingeniería Inversa & Laboratorio:** `jadx` (descompilador Java), `apktool`, `openjdk-17`, `gradle`.
* 📶 **Sniffers Wi-Fi/Red:** `tcpdump`, `tshark` (Wireshark CLI).

### 🎨 5. Estética, Shell & UI Restaurable
* 🐟 **Shell:** `fish` con Oh My Posh, Fastfetch y temas personalizados.
* 🎛️ **UI & Teclado:** Restauración de teclas extras con NerdFonts (`󰥻`, `󰯌`, ``, `󱎸`, ``, `󱞂`), márgenes y proporciones milimétricas.
* 📱 **Pinned Apps:** Respaldador y restaurador de las 12 aplicaciones ancladas del Launcher (WhatsApp, Brave, ChatGPT, Nequi, APatch, etc.).
* 📋 **Scripts de Utilidad:** `horario`, `gif-selector`, `portapapeles.sh` (con `fzf`).

---

## ⚡ Instalación Rápida (One-Liner)

En una instalación limpia de Termux, copia y pega este comando:

```bash
termux-setup-storage && pkg update -y && pkg install -y git && git clone https://github.com/javiermurciae-source/termux-setup.git ~/termux-setup && bash ~/termux-setup/setup-todo
```

---

## 🔄 Sincronización de Actualizaciones

Una vez instalado, el alias maestro queda registrado permanentemente en Fish. Para actualizar cambios desde GitHub, solo ejecuta:

```bash
sync-setup
```

---

## 📁 Estructura del Repositorio

```text
termux-setup/
├── setup-todo              # Script maestro de aprovisionamiento
├── README.md               # Documentación completa
├── fastfetch/              # Configuraciones de fastfetch y assets
├── termux_config/          # Configuración base de termux.properties
├── portapapeles/           # Utilidad flotante de portapapeles FZF
└── scripts/                # Scripts utilitarios auxiliares
```

---
*Desarrollado y optimizado para Infinix & arquitecturas ARM64 con soporte Root/Apatch.* 🚀
