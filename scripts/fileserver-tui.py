#!/usr/bin/env python3
"""
FileServer TUI - Terminal User Interface
Gestor de archivos con interfaz de terminal para compartir por red

Uso:
  python fileserver-tui.py                    # Sirve ~/storage
  python fileserver-tui.py /ruta/carpeta      # Sirve esa carpeta
  python fileserver-tui.py --port 9090        # Puerto personalizado
  python fileserver-tui.py --no-server        # Solo TUI, sin servidor web
"""

import curses
import os
import sys
import json
import time
import signal
import argparse
import socket
import subprocess
import threading
import mimetypes
import urllib.parse
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler

# ─── Globals ──────────────────────────────────────────────
BASE_DIR = ""
PORT = 8080
FILE_LIST = []
SELECTED = 0
SCROLL = 0
SORT_BY = "name"  # name, size, date
SORT_REV = False
SHOW_HIDDEN = False
STATUS_MSG = ""
STATUS_COLOR = 2
SERVER_RUNNING = True
PROCESO_INFO = {}

def human_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:>7.1f} {unit}"
        size /= 1024
    return f"{size:>7.1f} TB"

def file_icon(name, is_dir):
    if is_dir:
        return "📁"
    ext = Path(name).suffix.lower()
    icons = {
        '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📝',
        '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
        '.jpg': '🖼️ ', '.jpeg': '🖼️ ', '.png': '🖼️ ', '.gif': '🖼️ ',
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.m4a': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦',
        '.py': '🐍', '.js': '⚡', '.html': '🌐', '.css': '🎨',
        '.sh': '⚙️ ', '.bash': '⚙️ ',
        '.eap': '🏗️ ', '.eapx': '🏗️ ', '.apk': '📱',
        '.md': '📖', '.json': '📋', '.xml': '📋',
        '.ttf': '🔤', '.otf': '🔤',
    }
    return icons.get(ext, '📄')

def get_local_ip():
    try:
        r = subprocess.run(["tailscale-cli", "ip", "-4"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            return r.stdout.strip()
    except:
        pass
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "localhost"

def get_hostname():
    try:
        r = subprocess.run(["tailscale-cli", "status"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            for line in r.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] != 'hostname':
                    return parts[1]
    except:
        pass
    try:
        return socket.gethostname()
    except:
        return "unknown"

def scan_files():
    global FILE_LIST, PROCESO_INFO
    FILE_LIST = []
    try:
        entries = sorted(os.listdir(BASE_DIR))
    except PermissionError:
        return
    
    for entry in entries:
        if not SHOW_HIDDEN and entry.startswith('.'):
            continue
        full = os.path.join(BASE_DIR, entry)
        is_dir = os.path.isdir(full)
        try:
            stat = os.stat(full)
            size = stat.st_size if not is_dir else 0
            mtime = stat.st_mtime
        except:
            size = 0
            mtime = 0
        
        FILE_LIST.append({
            'name': entry,
            'is_dir': is_dir,
            'size': size,
            'mtime': mtime,
            'date': datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M'),
        })
    
    # Sort
    def sort_key(f):
        if f['is_dir']:
            return (0, f['name'].lower())
        if SORT_BY == 'size':
            return (1, f['size'])
        elif SORT_BY == 'date':
            return (1, f['mtime'])
        return (1, f['name'].lower())
    
    FILE_LIST.sort(key=sort_key, reverse=SORT_REV)
    
    # Get process info
    PROCESO_INFO = {}
    try:
        r = subprocess.run(["pgrep", "-a", "fileserver"], capture_output=True, text=True, timeout=3)
        for line in r.stdout.strip().split('\n'):
            if 'fileserver' in line:
                parts = line.split()
                if len(parts) >= 2:
                    PROCESO_INFO['pid'] = parts[0]
    except:
        pass

def draw_header(stdscr, height, width):
    """Draw the header bar"""
    hostname = get_hostname()
    ip = get_local_ip()
    dir_count = sum(1 for f in FILE_LIST if f['is_dir'])
    file_count = len(FILE_LIST) - dir_count
    total_size = sum(f['size'] for f in FILE_LIST if not f['is_dir'])
    
    try:
        # Title bar
        title = " [ FileServer TUI ] "
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addnstr(0, 0, title.ljust(width), width)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
        
        # Info bar
        info = f" {hostname} ({ip}:{PORT}) | {BASE_DIR} | {dir_count}d {file_count}f {human_size(total_size)}"
        stdscr.attron(curses.color_pair(5))
        stdscr.addnstr(1, 0, info.ljust(width), width)
        stdscr.attroff(curses.color_pair(5))
        
        # Separator
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(2, 0, "-" * width, width)
        stdscr.attroff(curses.color_pair(1))
    except curses.error:
        pass

def draw_columns(stdscr, width):
    """Draw column headers"""
    y = 3
    try:
        cols = f" {'Icon':<4} {'Name':<40} {'Size':>10} {'Date':<16} {'Type':<6}"
        stdscr.attron(curses.color_pair(3) | curses.A_BOLD)
        stdscr.addnstr(y, 0, cols.ljust(width), width)
        stdscr.attroff(curses.color_pair(3) | curses.A_BOLD)
        
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(y + 1, 0, "-" * width, width)
        stdscr.attroff(curses.color_pair(1))
    except curses.error:
        pass

def draw_files(stdscr, height, width):
    """Draw file list"""
    global SCROLL, SELECTED
    
    start_y = 5
    max_rows = height - start_y - 3  # Leave room for status bar
    
    # Clamp selection
    if SELECTED < 0:
        SELECTED = 0
    if SELECTED >= len(FILE_LIST):
        SELECTED = max(0, len(FILE_LIST) - 1)
    
    # Adjust scroll
    if SELECTED < SCROLL:
        SCROLL = SELECTED
    if SELECTED >= SCROLL + max_rows:
        SCROLL = SELECTED - max_rows + 1
    
    for i in range(max_rows):
        idx = SCROLL + i
        y = start_y + i
        
        if idx >= len(FILE_LIST):
            # Empty line
            stdscr.addnstr(y, 0, " " * width, width)
            continue
        
        f = FILE_LIST[idx]
        icon = "D" if f['is_dir'] else "F"
        name = f['name']
        if f['is_dir']:
            name += "/"
        
        max_name = width - 40
        if len(name) > max_name:
            name = name[:max_name-2] + ".."
        
        size_str = human_size(f['size']) if not f['is_dir'] else "  <DIR>"
        ext = Path(f['name']).suffix.upper().replace('.', '') if not f['is_dir'] else "DIR"
        if len(ext) > 6:
            ext = ext[:6]
        
        line = f" {icon} {name:<{max_name}} {size_str:>10} {f['date']:<16} {ext:<6}"
        
        try:
            if idx == SELECTED:
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addnstr(y, 0, line.ljust(width), width)
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            elif f['is_dir']:
                stdscr.attron(curses.color_pair(4))
                stdscr.addnstr(y, 0, line.ljust(width), width)
                stdscr.attroff(curses.color_pair(4))
            else:
                stdscr.addnstr(y, 0, line.ljust(width), width)
        except curses.error:
            break

def draw_status(stdscr, height, width):
    """Draw status bar"""
    global STATUS_MSG, STATUS_COLOR
    
    # Separator
    y = height - 3
    try:
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(y, 0, "-" * width, width)
        stdscr.attroff(curses.color_pair(1))
        
        if STATUS_MSG:
            stdscr.attron(curses.color_pair(STATUS_COLOR) | curses.A_BOLD)
            stdscr.addnstr(y + 1, 0, f" {STATUS_MSG}".ljust(width), width)
            stdscr.attroff(curses.color_pair(STATUS_COLOR) | curses.A_BOLD)
        else:
            proc = "ON" if PROCESO_INFO.get('pid') else "OFF"
            sort_label = {"name": "Name", "size": "Size", "date": "Date"}[SORT_BY]
            status = f" Server: {proc} | Sort: {sort_label}{'<' if not SORT_REV else '>'} | Hidden: {'ON' if SHOW_HIDDEN else 'OFF'}"
            stdscr.addnstr(y + 1, 0, status.ljust(width), width)
    except curses.error:
        pass
    
    try:
        help_text = " Up/Dn:Nav Enter:Open d:Del r:Ren n:Dir s:Sort ?:Help q:Quit "
        stdscr.attron(curses.color_pair(5))
        ht = help_text.center(width)
        stdscr.addnstr(y + 2, 0, ht[:width], width)
        stdscr.attroff(curses.color_pair(5))
    except curses.error:
        pass

def show_help(stdscr, height, width):
    """Show help overlay"""
    help_lines = [
        ("", ""),
        ("  FileServer TUI - Ayuda", 1),
        ("", ""),
        ("  Navegación:", 3),
        ("    ↑/k  Arriba", 0),
        ("    ↓/j  Abajo", 0),
        ("    Enter  Abrir carpeta / Ir atrás", 0),
        ("    Backspace  Ir a carpeta padre", 0),
        ("    ~  Ir al home", 0),
        ("", ""),
        ("  Archivos:", 3),
        ("    d  Eliminar archivo/carpeta", 0),
        ("    r  Renombrar", 0),
        ("    n  Nueva carpeta", 0),
        ("    Space  Info del archivo", 0),
        ("", ""),
        ("  Configuración:", 3),
        ("    s  Cambiar orden (nombre/tamaño/fecha)", 0),
        ("    R  Invertir orden", 0),
        ("    H  Mostrar/ocultar archivos ocultos", 0),
        ("", ""),
        ("  Red:", 3),
        ("    S  Iniciar/detener servidor web", 0),
        ("", ""),
        ("  Otros:", 3),
        ("    ?  Esta ayuda", 0),
        ("    q  Salir", 0),
        ("", ""),
        ("  Presiona cualquier tecla para cerrar", 5),
    ]
    
    # Box
    box_h = len(help_lines) + 2
    box_w = 55
    start_y = (height - box_h) // 2
    start_x = (width - box_w) // 2
    
    # Draw box
    for i in range(box_h):
        y = start_y + i
        if i == 0:
            line = "+" + "─" * (box_w - 2) + "+"
        elif i == box_h - 1:
            line = "+" + "─" * (box_w - 2) + "+"
        else:
            content = help_lines[i-1][0] if i-1 < len(help_lines) else ""
            color = help_lines[i-1][1] if i-1 < len(help_lines) else 0
            line = "|" + content.ljust(box_w - 2) + "|"
        
        if i == 0 or i == box_h - 1:
            stdscr.attron(curses.color_pair(1))
            stdscr.addnstr(y, start_x, line, box_w)
            stdscr.attroff(curses.color_pair(1))
        elif color:
            stdscr.attron(curses.color_pair(color) | curses.A_BOLD)
            stdscr.addnstr(y, start_x, line, box_w)
            stdscr.attroff(curses.color_pair(color) | curses.A_BOLD)
        else:
            stdscr.addnstr(y, start_x, line, box_w)
    
    stdscr.refresh()
    stdscr.getch()

def confirm_delete(stdscr, height, width, name):
    """Show delete confirmation"""
    msg = f" ¿Eliminar '{name}'? (y/N) "
    x = (width - len(msg)) // 2
    y = height // 2
    
    stdscr.attron(curses.color_pair(6) | curses.A_BOLD)
    stdscr.addnstr(y, x, msg, len(msg))
    stdscr.attroff(curses.color_pair(6) | curses.A_BOLD)
    stdscr.refresh()
    
    ch = stdscr.getch()
    return ch in (ord('y'), ord('Y'))

def prompt_input(stdscr, height, width, prompt, default=""):
    """Show input prompt"""
    curses.echo()
    curses.curs_set(1)
    
    msg = f" {prompt}: {default} "
    x = max(0, (width - len(msg) - 20) // 2)
    y = height // 2
    
    stdscr.attron(curses.color_pair(5) | curses.A_BOLD)
    stdscr.addnstr(y, x, msg, width - x)
    stdscr.attroff(curses.color_pair(5) | curses.A_BOLD)
    stdscr.refresh()
    
    # Get input
    stdscr.move(y, x + len(prompt) + 3)
    stdscr.clrtoeol()
    input_str = stdscr.getstr(y, x + len(prompt) + 3, 50).decode('utf-8', errors='replace')
    
    curses.noecho()
    curses.curs_set(0)
    return input_str if input_str else default

def show_file_info(stdscr, height, width, f):
    """Show file info overlay"""
    full = os.path.join(BASE_DIR, f['name'])
    lines = [
        f"  Nombre:  {f['name']}",
        f"  Tipo:    {'Carpeta' if f['is_dir'] else Path(f['name']).suffix.upper() or 'Sin extensión'}",
        f"  Tamaño:  {human_size(f['size']) if not f['is_dir'] else '<DIR>'}",
        f"  Modificado: {f['date']}",
        f"  Ruta:    {full}",
    ]
    
    box_h = len(lines) + 4
    box_w = max(50, max(len(l) for l in lines) + 6)
    start_y = (height - box_h) // 2
    start_x = (width - box_w) // 2
    
    for i in range(box_h):
        y = start_y + i
        if i == 0:
            line = "+" + "─" * (box_w - 2) + "+"
            stdscr.attron(curses.color_pair(1))
            stdscr.addnstr(y, start_x, line, box_w)
            stdscr.attroff(curses.color_pair(1))
        elif i == box_h - 1:
            line = "+" + "─" * (box_w - 2) + "+"
            stdscr.attron(curses.color_pair(1))
            stdscr.addnstr(y, start_x, line, box_w)
            stdscr.attroff(curses.color_pair(1))
        elif i - 1 < len(lines):
            content = lines[i-1]
            stdscr.addnstr(y, start_x, "|" + content.ljust(box_w - 2) + "|", box_w)
    
    stdscr.refresh()
    stdscr.getch()

# ─── HTTP Server (background) ────────────────────────────
class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass  # Silence HTTP logs in TUI
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rel = urllib.parse.unquote(parsed.path.lstrip('/'))
        full = os.path.join(BASE_DIR, rel)
        
        if 'getip' in query:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ip": get_local_ip(), "hostname": get_hostname()}).encode())
            return
        
        if os.path.isdir(full):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(self._dir_html(full, rel).encode())
        elif os.path.isfile(full):
            mime, _ = mimetypes.guess_type(full)
            size = os.path.getsize(full)
            self.send_response(200)
            self.send_header('Content-Type', mime or 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(full)}"')
            self.send_header('Content-Length', str(size))
            self.end_headers()
            with open(full, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_error(404)
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rel = urllib.parse.unquote(parsed.path.lstrip('/'))
        dest = os.path.join(BASE_DIR, rel)
        
        if 'upload' in query:
            ct = self.headers['Content-Type']
            if 'multipart/form-data' not in ct:
                self.send_error(400)
                return
            boundary = ct.split('boundary=')[1].encode()
            cl = int(self.headers['Content-Length'])
            body = self.rfile.read(cl)
            parts = body.split(b'--' + boundary)
            uploaded = []
            for part in parts[2:]:
                if b'filename="' not in part:
                    continue
                h_end = part.find(b'\r\n\r\n')
                if h_end == -1:
                    continue
                header = part[:h_end].decode('utf-8', errors='replace')
                data = part[h_end+4:]
                if data.endswith(b'\r\n'):
                    data = data[:-2]
                fn_s = header.find('filename="') + 10
                fn_e = header.find('"', fn_s)
                filename = header[fn_s:fn_e]
                if filename:
                    os.makedirs(dest, exist_ok=True)
                    with open(os.path.join(dest, filename), 'wb') as f:
                        f.write(data)
                    uploaded.append(filename)
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"uploaded": uploaded}).encode())
    
    def _dir_html(self, dpath, rel):
        items = []
        for e in sorted(os.listdir(dpath)):
            fp = os.path.join(dpath, e)
            is_d = os.path.isdir(fp)
            er = os.path.join(rel, e) if rel else e
            items.append(f'<li><a href="/{urllib.parse.quote(er)}{"./" if is_d else "?download=true"}">{file_icon(e, is_d)} {e}{" /" if is_d else ""}</a></li>')
        return f"""<!DOCTYPE html><html><head><meta charset="utf-8"><title>📁 {rel or 'Home'}</title>
<style>body{{font-family:monospace;background:#0f172a;color:#e2e8f0;padding:20px}}
a{{color:#60a5fa;text-decoration:none}}a:hover{{text-decoration:underline}}
li{{padding:5px 0;font-size:1.1em}}</style></head>
<body><h1>📁 {rel or 'Home'}</h1><ul>{"".join(items)}</ul></body></html>"""

def start_server():
    global SERVER_RUNNING
    try:
        server = HTTPServer(("0.0.0.0", PORT), QuietHandler)
        server.timeout = 1
        while SERVER_RUNNING:
            server.handle_request()
        server.server_close()
    except:
        pass

# ─── Main TUI ─────────────────────────────────────────────
def main(stdscr):
    global SELECTED, SCROLL, SORT_BY, SORT_REV, SHOW_HIDDEN
    global STATUS_MSG, STATUS_COLOR, SERVER_RUNNING
    
    # Colors
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLUE, -1)      # Header/separator
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)  # Selected
    curses.init_pair(3, curses.COLOR_YELLOW, -1)     # Column headers
    curses.init_pair(4, curses.COLOR_GREEN, -1)      # Directories
    curses.init_pair(5, curses.COLOR_WHITE, -1)      # Info
    curses.init_pair(6, curses.COLOR_RED, -1)        # Warning
    
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(-1)
    
    scan_files()
    
    while True:
        height, width = stdscr.getmaxyx()
        stdscr.erase()
        
        draw_header(stdscr, height, width)
        draw_columns(stdscr, width)
        draw_files(stdscr, height, width)
        draw_status(stdscr, height, width)
        
        stdscr.refresh()
        
        ch = stdscr.getch()
        STATUS_MSG = ""
        
        if ch == ord('q') or ch == ord('Q'):
            SERVER_RUNNING = False
            break
        
        elif ch in (curses.KEY_UP, ord('k')):
            SELECTED = max(0, SELECTED - 1)
        
        elif ch in (curses.KEY_DOWN, ord('j')):
            SELECTED = min(len(FILE_LIST) - 1, SELECTED + 1)
        
        elif ch in (curses.KEY_ENTER, 10, 13):
            if FILE_LIST:
                f = FILE_LIST[SELECTED]
                if f['is_dir']:
                    new_dir = os.path.join(BASE_DIR, f['name'])
                    if f['name'] == '..':
                        new_dir = os.path.dirname(BASE_DIR.rstrip('/'))
                    BASE_DIR = new_dir
                    SELECTED = 0
                    SCROLL = 0
                    scan_files()
                    STATUS_MSG = f"📂 {BASE_DIR}"
                    STATUS_COLOR = 4
        
        elif ch == curses.KEY_BACKSPACE or ch == 127:
            parent = os.path.dirname(BASE_DIR.rstrip('/'))
            if parent and parent != BASE_DIR:
                BASE_DIR = parent
                SELECTED = 0
                SCROLL = 0
                scan_files()
                STATUS_MSG = f"📂 {BASE_DIR}"
                STATUS_COLOR = 4
        
        elif ch == ord('~'):
            BASE_DIR = os.path.expanduser("~")
            SELECTED = 0
            SCROLL = 0
            scan_files()
            STATUS_MSG = f"📂 {BASE_DIR}"
            STATUS_COLOR = 4
        
        elif ch == ord('s') or ch == ord('S'):
            if ch == ord('S'):
                # Start/stop server
                if PROCESO_INFO.get('pid'):
                    subprocess.run(["kill", PROCESO_INFO['pid']], capture_output=True)
                    PROCESO_INFO = {}
                    STATUS_MSG = "🔴 Servidor detenido"
                    STATUS_COLOR = 6
                else:
                    subprocess.Popen(
                        ["python3", os.path.abspath(__file__), BASE_DIR, "--port", str(PORT), "--no-tui"],
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
                    )
                    time.sleep(0.5)
                    scan_files()
                    STATUS_MSG = f"🟢 Servidor iniciado en :{PORT}"
                    STATUS_COLOR = 4
            else:
                # Sort cycle
                if SORT_BY == "name":
                    SORT_BY = "size"
                elif SORT_BY == "size":
                    SORT_BY = "date"
                else:
                    SORT_BY = "name"
                SELECTED = 0
                SCROLL = 0
                scan_files()
                STATUS_MSG = f"📋 Ordenado por: {SORT_BY}"
                STATUS_COLOR = 3
        
        elif ch == ord('R'):
            SORT_REV = not SORT_REV
            SELECTED = 0
            SCROLL = 0
            scan_files()
            STATUS_MSG = f"🔄 Orden {'invertido' if SORT_REV else 'normal'}"
            STATUS_COLOR = 3
        
        elif ch == ord('h') or ch == ord('H'):
            if ch == 'H':
                pass
            SHOW_HIDDEN = not SHOW_HIDDEN
            SELECTED = 0
            SCROLL = 0
            scan_files()
            STATUS_MSG = f"👁️ Ocultos: {'MOSTRANDO' if SHOW_HIDDEN else 'OCULTOS'}"
            STATUS_COLOR = 3
        
        elif ch == ord('d') or ch == ord('D'):
            if FILE_LIST:
                f = FILE_LIST[SELECTED]
                if confirm_delete(stdscr, height, width, f['name']):
                    full = os.path.join(BASE_DIR, f['name'])
                    try:
                        if f['is_dir']:
                            import shutil
                            shutil.rmtree(full)
                        else:
                            os.remove(full)
                        scan_files()
                        STATUS_MSG = f"🗑️ Eliminado: {f['name']}"
                        STATUS_COLOR = 6
                    except Exception as e:
                        STATUS_MSG = f"❌ Error: {e}"
                        STATUS_COLOR = 6
        
        elif ch == ord('r'):
            if FILE_LIST:
                f = FILE_LIST[SELECTED]
                new_name = prompt_input(stdscr, height, width, "Renombrar", f['name'])
                if new_name and new_name != f['name']:
                    old = os.path.join(BASE_DIR, f['name'])
                    new = os.path.join(BASE_DIR, new_name)
                    try:
                        os.rename(old, new)
                        scan_files()
                        STATUS_MSG = f"✏️ Renombrado: {f['name']} → {new_name}"
                        STATUS_COLOR = 4
                    except Exception as e:
                        STATUS_MSG = f"❌ Error: {e}"
                        STATUS_COLOR = 6
        
        elif ch == ord('n'):
            dirname = prompt_input(stdscr, height, width, "Nueva carpeta")
            if dirname:
                try:
                    os.makedirs(os.path.join(BASE_DIR, dirname), exist_ok=True)
                    scan_files()
                    STATUS_MSG = f"📁 Carpeta creada: {dirname}"
                    STATUS_COLOR = 4
                except Exception as e:
                    STATUS_MSG = f"❌ Error: {e}"
                    STATUS_COLOR = 6
        
        elif ch == ord(' '):
            if FILE_LIST:
                show_file_info(stdscr, height, width, FILE_LIST[SELECTED])
        
        elif ch == ord('?'):
            show_help(stdscr, height, width)
        
        elif ch == curses.KEY_RESIZE:
            stdscr.clear()

# ─── Entry ────────────────────────────────────────────────
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FileServer TUI")
    parser.add_argument("directory", nargs="?", default=os.path.expanduser("~/storage"))
    parser.add_argument("--port", "-p", type=int, default=8080)
    parser.add_argument("--no-tui", action="store_true", help="Run server only (no TUI)")
    args = parser.parse_args()
    
    BASE_DIR = os.path.abspath(args.directory)
    PORT = args.port
    
    if not os.path.isdir(BASE_DIR):
        print(f"❌ Carpeta no encontrada: {BASE_DIR}")
        sys.exit(1)
    
    if args.no_tui:
        # Server-only mode
        server = HTTPServer(("0.0.0.0", PORT), QuietHandler)
        server.serve_forever()
    else:
        # Start server in background
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        ip = get_local_ip()
        hostname = get_hostname()
        
        # Run TUI
        try:
            curses.wrapper(main)
        except KeyboardInterrupt:
            pass
        finally:
            SERVER_RUNNING = False
            print(f"\n📁 FileServer detenido.")
            print(f"   Server: http://{hostname}:{PORT}")
