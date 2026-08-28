#!/usr/bin/env python3
"""
FileServer TUI - Estilo Yazi
File manager de terminal con interfaz de dos paneles
Soporte local y remoto (via Tailscale SOCKS5)
"""

import curses
import os
import sys
import json
import time
import argparse
import subprocess
import mimetypes
from pathlib import Path
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import urllib.request
import threading
import socket

# --- Globals ---
BASE_DIR = ""
PORT = 8080
REMOTE_HOST = ""
REMOTE_PORT = 8080
REMOTE_MODE = False
SERVER_RUNNING = True

# --- State ---
DIRS = []
FILES = []
SELECTED = 0
SCROLL = 0
PREVIEW_LINES = []
STATUS_MSG = ""
STATUS_COLOR = 2
SORT_BY = "name"
SORT_REV = False
SHOW_HIDDEN = False

def human_size(size):
    for u in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {u}"
        size /= 1024
    return f"{size:.1f} TB"

def file_ext(name):
    return Path(name).suffix.lower()

def safe_size(path):
    try:
        return human_size(os.path.getsize(path))
    except:
        return '?'

def get_preview(name, is_dir, full_path):
    ext = file_ext(name)
    if is_dir:
        try:
            entries = os.listdir(full_path)
            dirs = [e for e in entries if os.path.isdir(os.path.join(full_path, e))]
            files = [e for e in entries if not os.path.isdir(os.path.join(full_path, e))]
            lines = [f"  {len(dirs)} dirs, {len(files)} files"]
            for e in sorted(entries)[:15]:
                p = os.path.join(full_path, e)
                d = "[DIR]" if os.path.isdir(p) else human_size(os.path.getsize(p))
                lines.append(f"  {e[:30]}  {d}")
            if len(entries) > 15:
                lines.append(f"  ... +{len(entries)-15} more")
            return lines
        except:
            return ["  [Permission denied]"]
    elif ext in ('.txt', '.md', '.py', '.sh', '.json', '.xml', '.csv', '.log', '.conf', '.cfg', '.ini', '.yaml', '.yml', '.toml'):
        try:
            with open(full_path, 'r', errors='replace') as f:
                lines = [l.rstrip()[:60] for _, l in zip(range(20), f)]
            return lines
        except:
            return ["  [Cannot read]"]
    elif ext in ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'):
        return ["  [Image]", f"  {ext.upper()}", f"  {safe_size(full_path)}"]
    elif ext in ('.mp4', '.avi', '.mkv', '.mov', '.webm'):
        return ["  [Video]", f"  {ext.upper()}", f"  {safe_size(full_path)}"]
    elif ext in ('.mp3', '.wav', '.ogg', '.m4a', '.flac'):
        return ["  [Audio]", f"  {ext.upper()}", f"  {safe_size(full_path)}"]
    elif ext in ('.zip', '.tar', '.gz', '.rar', '.7z'):
        return ["  [Archive]", f"  {ext.upper()}", f"  {safe_size(full_path)}"]
    elif ext in ('.pdf',):
        return ["  [PDF]", f"  {safe_size(full_path)}"]
    elif ext in ('.eap', '.eapx'):
        return ["  [Enterprise Architect]", f"  {safe_size(full_path)}"]
    elif ext in ('.apk',):
        return ["  [Android Package]", f"  {safe_size(full_path)}"]
    else:
        return ["  [File]", f"  {ext or 'no ext'}", f"  {safe_size(full_path)}"]

def scan_local():
    global DIRS, FILES
    DIRS = []
    FILES = []
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
        item = {'name': entry, 'is_dir': is_dir, 'size': size, 'mtime': mtime}
        if is_dir:
            DIRS.append(item)
        else:
            FILES.append(item)
    sort_items()

def scan_remote():
    global DIRS, FILES, STATUS_MSG
    DIRS = []
    FILES = []
    try:
        path = BASE_DIR if BASE_DIR.startswith('/') else '/' + BASE_DIR
        url = f"http://{REMOTE_HOST}:{REMOTE_PORT}{path}?json=true"
        r = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5",
             "--socks5-hostname", "127.0.0.1:1055", url],
            capture_output=True, text=True, timeout=10
        )
        if r.returncode != 0 or not r.stdout.strip():
            STATUS_MSG = "Connection error"
            return
        data = json.loads(r.stdout)
        for item in data.get('items', []):
            if not SHOW_HIDDEN and item['name'].startswith('.'):
                continue
            if item['is_dir']:
                DIRS.append(item)
            else:
                FILES.append(item)
    except Exception as e:
        STATUS_MSG = str(e)[:50]
    sort_items()

def sort_items():
    def key(d):
        return d['name'].lower()
    if SORT_BY == 'size':
        def key(d): return (0 if d['is_dir'] else 1, d['size'])
    elif SORT_BY == 'date':
        def key(d): return (0 if d['is_dir'] else 1, d['mtime'])
    DIRS.sort(key=key, reverse=SORT_REV)
    FILES.sort(key=key, reverse=SORT_REV)

def get_all_items():
    return DIRS + FILES

def download_file(name):
    if REMOTE_MODE:
        path = BASE_DIR if BASE_DIR.startswith('/') else '/' + BASE_DIR
        url = f"http://{REMOTE_HOST}:{REMOTE_PORT}{path}/{name}"
        dest = os.path.expanduser(f"~/storage/downloads/{name}")
        r = subprocess.run(
            ["curl", "-s", "-L", "--connect-timeout", "10",
             "--socks5-hostname", "127.0.0.1:1055", "-o", dest, url],
            capture_output=True, text=True, timeout=30
        )
        if r.returncode == 0 and os.path.exists(dest):
            return True, dest
        return False, "Download failed"
    else:
        src = os.path.join(BASE_DIR, name)
        dest = os.path.expanduser(f"~/storage/downloads/{name}")
        try:
            import shutil
            shutil.copy2(src, dest)
            return True, dest
        except Exception as e:
            return False, str(e)

def draw_ui(stdscr, height, width):
    global SELECTED, SCROLL, STATUS_MSG, STATUS_COLOR
    stdscr.erase()
    left_w = width // 2
    right_w = width - left_w

    items = get_all_items()
    total = len(items)

    # Clamp
    if SELECTED < 0:
        SELECTED = 0
    if SELECTED >= total:
        SELECTED = max(0, total - 1)

    max_rows = height - 3
    if SELECTED < SCROLL:
        SCROLL = SELECTED
    if SELECTED >= SCROLL + max_rows:
        SCROLL = SELECTED - max_rows + 1

    # --- Header ---
    header = f" FileServer TUI "
    remote_tag = f" [REMOTE: {REMOTE_HOST}]" if REMOTE_MODE else ""
    dir_info = f" {BASE_DIR} "
    stats = f" {len(DIRS)}d {len(FILES)}f "
    hdr = f"{header}{remote_tag}{dir_info}{stats}"
    try:
        stdscr.attron(curses.color_pair(1) | curses.A_BOLD)
        stdscr.addnstr(0, 0, hdr.center(width)[:width], width)
        stdscr.attroff(curses.color_pair(1) | curses.A_BOLD)
    except curses.error:
        pass

    # --- Left panel: file list ---
    try:
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(1, 0, "-" * left_w, left_w)
        stdscr.attroff(curses.color_pair(1))
    except curses.error:
        pass

    for i in range(max_rows):
        y = 2 + i
        idx = SCROLL + i
        try:
            if idx >= total:
                stdscr.addnstr(y, 0, " " * left_w, left_w)
                continue
            item = items[idx]
            name = item['name']
            if item['is_dir']:
                name += "/"
            max_name = left_w - 12
            if len(name) > max_name:
                name = name[:max_name-2] + ".."
            size = " <DIR>" if item['is_dir'] else human_size(item['size'])[:8]
            line = f" {name:<{max_name}} {size:>8} "
            if idx == SELECTED:
                stdscr.attron(curses.color_pair(2) | curses.A_BOLD)
                stdscr.addnstr(y, 0, line[:left_w], left_w)
                stdscr.attroff(curses.color_pair(2) | curses.A_BOLD)
            elif item['is_dir']:
                stdscr.attron(curses.color_pair(4))
                stdscr.addnstr(y, 0, line[:left_w], left_w)
                stdscr.attroff(curses.color_pair(4))
            else:
                stdscr.addnstr(y, 0, line[:left_w], left_w)
        except curses.error:
            break

    # --- Right panel: preview ---
    try:
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(1, left_w, "-" * right_w, right_w)
        stdscr.attroff(curses.color_pair(1))
    except curses.error:
        pass

    if items:
        item = items[SELECTED]
        full = os.path.join(BASE_DIR, item['name']) if not REMOTE_MODE else item['name']
        preview = get_preview(item['name'], item['is_dir'], full)
        for i in range(max_rows):
            y = 2 + i
            try:
                if i < len(preview):
                    line = preview[i][:right_w-1]
                    stdscr.addnstr(y, left_w, f" {line}", right_w)
                else:
                    stdscr.addnstr(y, left_w, " " * right_w, right_w)
            except curses.error:
                break
    else:
        try:
            stdscr.addnstr(2, left_w, " Empty", right_w)
        except curses.error:
            pass

    # --- Status bar ---
    try:
        y = height - 2
        stdscr.attron(curses.color_pair(1))
        stdscr.addnstr(y, 0, "-" * width, width)
        stdscr.attroff(curses.color_pair(1))

        if STATUS_MSG:
            stdscr.attron(curses.color_pair(STATUS_COLOR) | curses.A_BOLD)
            stdscr.addnstr(y + 1, 0, f" {STATUS_MSG}".ljust(width), width)
            stdscr.attroff(curses.color_pair(STATUS_COLOR) | curses.A_BOLD)
        else:
            sort_label = {"name": "Name", "size": "Size", "date": "Date"}[SORT_BY]
            hidden = "ON" if SHOW_HIDDEN else "OFF"
            status = f" h/j:Nav  Enter:Open  d:Download  H:Hidden  s:Sort  ?:Help  q:Quit | Sort:{sort_label} Hid:{hidden}"
            stdscr.addnstr(y + 1, 0, status[:width], width)
    except curses.error:
        pass

    stdscr.refresh()

def show_help(stdscr, height, width):
    lines = [
        "FileServer TUI - Help",
        "",
        "Navigation:",
        "  j/Down   Move down",
        "  k/Up     Move up",
        "  h/Left   Go to parent dir",
        "  l/Right  Enter directory / select",
        "  Enter    Enter directory / go back",
        "  Backspace  Parent directory",
        "  g        Go to top",
        "  G        Go to bottom",
        "",
        "Actions:",
        "  d        Download file to ~/storage/downloads/",
        "  Space    Download file (alias for d)",
        "  s        Sort by name/size/date",
        "  R        Reverse sort order",
        "  H        Toggle hidden files",
        "",
        "Remote:",
        "  S        Toggle web server on/off",
        "",
        "  q        Quit",
    ]
    box_w = min(width - 4, 55)
    box_h = len(lines) + 2
    sy = max(0, (height - box_h) // 2)
    sx = max(0, (width - box_w) // 2)
    try:
        for i in range(box_h):
            y = sy + i
            if i == 0:
                stdscr.attron(curses.color_pair(1))
                stdscr.addnstr(y, sx, "+" + "-" * (box_w - 2) + "+", box_w)
                stdscr.attroff(curses.color_pair(1))
            elif i == box_h - 1:
                stdscr.attron(curses.color_pair(1))
                stdscr.addnstr(y, sx, "+" + "-" * (box_w - 2) + "+", box_w)
                stdscr.attroff(curses.color_pair(1))
            elif i - 1 < len(lines):
                content = lines[i-1]
                color = 3 if i == 1 else (4 if content.endswith(":") else 0)
                if color:
                    stdscr.attron(curses.color_pair(color))
                stdscr.addnstr(y, sx, "|" + content.ljust(box_w - 2) + "|", box_w)
                if color:
                    stdscr.attroff(curses.color_pair(color))
        stdscr.refresh()
        stdscr.getch()
    except curses.error:
        pass

# --- HTTP Server ---
class QuietHandler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rel = urllib.parse.unquote(parsed.path.lstrip('/'))
        full = os.path.join(BASE_DIR, rel)
        if 'getip' in query:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"ip": "ok"}).encode())
            return
        if os.path.isdir(full) and 'json' in query:
            items = []
            try:
                for e in sorted(os.listdir(full)):
                    fp = os.path.join(full, e)
                    is_d = os.path.isdir(fp)
                    try:
                        st = os.stat(fp)
                        items.append({'name': e, 'is_dir': is_d, 'size': st.st_size if not is_d else 0, 'mtime': st.st_mtime, 'path': e})
                    except:
                        items.append({'name': e, 'is_dir': is_d, 'size': 0, 'mtime': 0, 'path': e})
            except:
                pass
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'path': rel or '/', 'items': items}).encode())
            return
        if os.path.isfile(full):
            mime, _ = mimetypes.guess_type(full)
            size = os.path.getsize(full)
            self.send_response(200)
            self.send_header('Content-Type', mime or 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{os.path.basename(full)}"')
            self.send_header('Content-Length', str(size))
            self.end_headers()
            with open(full, 'rb') as f:
                self.wfile.write(f.read())
        elif os.path.isdir(full):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<html><body><h1>Directory</h1></body></html>")
        else:
            self.send_error(404)

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

# --- Main ---
def main(stdscr):
    global SELECTED, SCROLL, SORT_BY, SORT_REV, SHOW_HIDDEN
    global STATUS_MSG, STATUS_COLOR, SERVER_RUNNING, BASE_DIR

    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(1, curses.COLOR_BLUE, -1)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_CYAN)
    curses.init_pair(3, curses.COLOR_YELLOW, -1)
    curses.init_pair(4, curses.COLOR_GREEN, -1)
    curses.init_pair(5, curses.COLOR_WHITE, -1)
    curses.init_pair(6, curses.COLOR_RED, -1)
    curses.curs_set(0)
    stdscr.keypad(True)
    stdscr.timeout(-1)

    if REMOTE_MODE:
        scan_remote()
    else:
        scan_local()

    while True:
        height, width = stdscr.getmaxyx()
        draw_ui(stdscr, height, width)
        ch = stdscr.getch()
        STATUS_MSG = ""
        items = get_all_items()
        total = len(items)

        if ch == ord('q') or ch == ord('Q'):
            SERVER_RUNNING = False
            break

        elif ch in (curses.KEY_DOWN, ord('j')):
            SELECTED = min(total - 1, SELECTED + 1)

        elif ch in (curses.KEY_UP, ord('k')):
            SELECTED = max(0, SELECTED - 1)

        elif ch in (curses.KEY_ENTER, 10, 13, ord('l'), curses.KEY_RIGHT):
            if items:
                item = items[SELECTED]
                if item['is_dir']:
                    if item['name'] == '..':
                        BASE_DIR = os.path.dirname(BASE_DIR.rstrip('/')) or '/'
                    else:
                        BASE_DIR = os.path.join(BASE_DIR, item['name']) if not BASE_DIR.endswith('/') else BASE_DIR + item['name']
                    SELECTED = 0
                    SCROLL = 0
                    if REMOTE_MODE:
                        scan_remote()
                    else:
                        scan_local()
                    STATUS_MSG = BASE_DIR
                    STATUS_COLOR = 4

        elif ch == curses.KEY_BACKSPACE or ch == 127 or ch == ord('h') or ch == curses.KEY_LEFT:
            parent = os.path.dirname(BASE_DIR.rstrip('/'))
            if parent and parent != BASE_DIR:
                BASE_DIR = parent or '/'
                SELECTED = 0
                SCROLL = 0
                if REMOTE_MODE:
                    scan_remote()
                else:
                    scan_local()
                STATUS_MSG = BASE_DIR
                STATUS_COLOR = 4

        elif ch in (ord('d'), ord(' '), ord('D')):
            if items:
                item = items[SELECTED]
                if not item['is_dir']:
                    STATUS_MSG = f"Downloading {item['name']}..."
                    STATUS_COLOR = 3
                    draw_ui(stdscr, height, width)
                    ok, result = download_file(item['name'])
                    if ok:
                        STATUS_MSG = f"Downloaded: {result}"
                        STATUS_COLOR = 4
                    else:
                        STATUS_MSG = f"Error: {result}"
                        STATUS_COLOR = 6

        elif ch == ord('s') or ch == ord('S'):
            if ch == ord('S'):
                # Toggle web server
                pass  # TODO
            else:
                if SORT_BY == "name":
                    SORT_BY = "size"
                elif SORT_BY == "size":
                    SORT_BY = "date"
                else:
                    SORT_BY = "name"
                SELECTED = 0
                SCROLL = 0
                if REMOTE_MODE:
                    scan_remote()
                else:
                    scan_local()

        elif ch == ord('R'):
            SORT_REV = not SORT_REV
            SELECTED = 0
            SCROLL = 0
            if REMOTE_MODE:
                scan_remote()
            else:
                scan_local()

        elif ch == ord('h') or ch == ord('H'):
            if ch == ord('H'):
                SHOW_HIDDEN = not SHOW_HIDDEN
                SELECTED = 0
                SCROLL = 0
                if REMOTE_MODE:
                    scan_remote()
                else:
                    scan_local()

        elif ch == ord('g'):
            SELECTED = 0
            SCROLL = 0

        elif ch == ord('G'):
            SELECTED = max(0, total - 1)

        elif ch == ord('?'):
            show_help(stdscr, height, width)

        elif ch == curses.KEY_RESIZE:
            stdscr.clear()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="FileServer TUI - Yazi style")
    parser.add_argument("directory", nargs="?", default=os.path.expanduser("~/storage"))
    parser.add_argument("--port", "-p", type=int, default=8080)
    parser.add_argument("--remote", "-r", help="Remote host")
    parser.add_argument("--remote-port", type=int, default=8080)
    parser.add_argument("--no-tui", action="store_true")
    args = parser.parse_args()

    PORT = args.port

    if args.remote:
        REMOTE_HOST = args.remote
        REMOTE_PORT = args.remote_port
        REMOTE_MODE = True
        BASE_DIR = args.directory if args.directory != os.path.expanduser("~/storage") else "/"
    else:
        BASE_DIR = os.path.abspath(args.directory)
        if not os.path.isdir(BASE_DIR):
            print(f"Not found: {BASE_DIR}")
            sys.exit(1)

    if args.no_tui:
        server = HTTPServer(("0.0.0.0", PORT), QuietHandler)
        server.serve_forever()
    else:
        t = threading.Thread(target=start_server, daemon=True)
        t.start()
        try:
            curses.wrapper(main)
        except KeyboardInterrupt:
            pass
        finally:
            SERVER_RUNNING = False
            print(f"\nFileServer stopped. Server was at :{PORT}")
