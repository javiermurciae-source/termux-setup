#!/usr/bin/env python3
"""
FileServer - Servidor web para compartir archivos
Accesible desde cualquier dispositivo en la red Tailscale

Uso:
  python fileserver.py                  # Sirve ~/storage en 0.0.0.0:8080
  python fileserver.py /ruta/carpeta    # Sirve esa carpeta
  python fileserver.py --port 9090      # Puerto personalizado
"""

import http.server
import os
import sys
import json
import hashlib
import urllib.parse
import mimetypes
import argparse
import socket
import subprocess
import time
from pathlib import Path
from io import BytesIO

PORT = 8080
BASE_DIR = ""

def get_local_ip():
    """Obtiene la IP local por Tailscale o wlan"""
    try:
        result = subprocess.run(
            ["tailscale-cli", "ip", "-4"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
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
    """Obtiene el hostname de Tailscale (estable, no cambia)"""
    try:
        result = subprocess.run(
            ["tailscale-cli", "status"],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0:
            for line in result.stdout.strip().split('\n'):
                parts = line.split()
                if len(parts) >= 2 and parts[1] != 'hostname':
                    return parts[1]
    except:
        pass
    try:
        return socket.gethostname()
    except:
        return "unknown"

def human_size(size):
    """Tamaño legible"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{size:.1f} PB"

def file_icon(name):
    """Icono según extensión"""
    ext = Path(name).suffix.lower()
    icons = {
        '.pdf': '📄', '.doc': '📝', '.docx': '📝', '.txt': '📝',
        '.xls': '📊', '.xlsx': '📊', '.csv': '📊',
        '.jpg': '🖼️', '.jpeg': '🖼️', '.png': '🖼️', '.gif': '🖼️',
        '.mp4': '🎬', '.avi': '🎬', '.mkv': '🎬', '.mov': '🎬',
        '.mp3': '🎵', '.wav': '🎵', '.ogg': '🎵', '.m4a': '🎵',
        '.zip': '📦', '.rar': '📦', '.7z': '📦', '.tar': '📦', '.gz': '📦',
        '.py': '🐍', '.js': '⚡', '.html': '🌐', '.css': '🎨',
        '.sh': '⚙️', '.bash': '⚙️',
        '.eap': '🏗️', '.eapx': '🏗️', '.apk': '📱',
        '.md': '📖', '.json': '📋', '.xml': '📋',
        '.ttf': '🔤', '.otf': '🔤',
    }
    return icons.get(ext, '📄')

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>📁 FileServer</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background: #0f172a; color: #e2e8f0;
    min-height: 100vh;
  }
  .header {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
    padding: 20px 30px;
    border-bottom: 2px solid #3b82f6;
    display: flex; align-items: center; justify-content: space-between;
    flex-wrap: wrap; gap: 10px;
  }
  .header h1 { font-size: 1.5rem; color: #60a5fa; }
  .header .info { font-size: 0.85rem; color: #94a3b8; }
  .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
  .breadcrumb {
    padding: 15px 0; font-size: 0.9rem; color: #94a3b8;
    display: flex; align-items: center; gap: 5px; flex-wrap: wrap;
  }
  .breadcrumb a { color: #60a5fa; text-decoration: none; }
  .breadcrumb a:hover { text-decoration: underline; }
  .actions {
    display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap;
  }
  .btn {
    padding: 10px 20px; border: none; border-radius: 8px;
    cursor: pointer; font-size: 0.9rem; font-weight: 600;
    transition: all 0.2s; text-decoration: none;
  }
  .btn-primary { background: #3b82f6; color: white; }
  .btn-primary:hover { background: #2563eb; }
  .btn-success { background: #22c55e; color: white; }
  .btn-success:hover { background: #16a34a; }
  .btn-danger { background: #ef4444; color: white; }
  .btn-danger:hover { background: #dc2626; }
  .upload-zone {
    border: 2px dashed #475569; border-radius: 12px;
    padding: 30px; text-align: center; margin-bottom: 20px;
    transition: all 0.2s; cursor: pointer;
  }
  .upload-zone:hover, .upload-zone.dragover {
    border-color: #3b82f6; background: rgba(59,130,246,0.1);
  }
  .upload-zone p { color: #94a3b8; margin-top: 10px; }
  .file-list { list-style: none; }
  .file-item {
    display: flex; align-items: center; gap: 15px;
    padding: 12px 16px; border-radius: 8px;
    transition: background 0.2s; border-bottom: 1px solid #1e293b;
  }
  .file-item:hover { background: #1e293b; }
  .file-icon { font-size: 1.5rem; min-width: 40px; text-align: center; }
  .file-info { flex: 1; min-width: 0; }
  .file-name {
    font-weight: 500; color: #f1f5f9;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  }
  .file-name a { color: #f1f5f9; text-decoration: none; }
  .file-name a:hover { color: #60a5fa; }
  .file-meta { font-size: 0.8rem; color: #64748b; margin-top: 2px; }
  .file-actions { display: flex; gap: 8px; }
  .file-actions .btn { padding: 6px 12px; font-size: 0.8rem; }
  .stats {
    display: flex; gap: 20px; padding: 15px 0;
    font-size: 0.85rem; color: #64748b; border-top: 1px solid #1e293b;
    margin-top: 20px;
  }
  #uploadProgress { display: none; margin: 10px 0; }
  .progress-bar {
    height: 6px; background: #1e293b; border-radius: 3px; overflow: hidden;
  }
  .progress-fill {
    height: 100%; background: #3b82f6; width: 0%; transition: width 0.3s;
  }
  @media (max-width: 600px) {
    .header { padding: 15px; }
    .header h1 { font-size: 1.2rem; }
    .file-item { gap: 10px; padding: 10px; }
    .actions { flex-direction: column; }
    .btn { width: 100%; text-align: center; }
  }
</style>
</head>
<body>
<div class="header">
  <h1>📁 FileServer</h1>
  <div class="info">
    🌐 <span id="ip">Cargando IP...</span> &nbsp;|&nbsp;
    🖥️ <span id="host">Cargando hostname...</span> &nbsp;|&nbsp;
    ⏱️ <span id="time"></span>
  </div>
</div>
<div class="container">
  <div class="breadcrumb" id="breadcrumb"></div>
  
  <div class="upload-zone" id="uploadZone" onclick="document.getElementById('fileInput').click()">
    <div style="font-size:2rem">📤</div>
    <p>Arrastra archivos aquí o haz click para subir</p>
    <input type="file" id="fileInput" multiple style="display:none" onchange="uploadFiles(this.files)">
  </div>
  
  <div id="uploadProgress">
    <div class="progress-bar"><div class="progress-fill" id="progressFill"></div></div>
    <p style="font-size:0.85rem;color:#94a3b8;margin-top:5px" id="uploadStatus">Subiendo...</p>
  </div>
  
  <div class="actions">
    <a class="btn btn-primary" href="?download_dir=true" id="downloadAll">📦 Descargar todo (ZIP)</a>
  </div>
  
  <ul class="file-list" id="fileList"></ul>
  
  <div class="stats" id="stats"></div>
</div>

<script>
const currentPath = window.location.pathname;
const baseUrl = window.location.origin;

document.getElementById('uploadZone').addEventListener('dragover', e => {
  e.preventDefault(); e.currentTarget.classList.add('dragover');
});
document.getElementById('uploadZone').addEventListener('dragleave', e => {
  e.currentTarget.classList.remove('dragover');
});
document.getElementById('uploadZone').addEventListener('drop', e => {
  e.preventDefault(); e.currentTarget.classList.remove('dragover');
  uploadFiles(e.dataTransfer.files);
});

function uploadFiles(files) {
  if (!files.length) return;
  const zone = document.getElementById('uploadZone');
  const progress = document.getElementById('uploadProgress');
  const fill = document.getElementById('progressFill');
  const status = document.getElementById('uploadStatus');
  
  progress.style.display = 'block';
  let uploaded = 0;
  
  for (const file of files) {
    const formData = new FormData();
    formData.append('file', file);
    
    const xhr = new XMLHttpRequest();
    xhr.open('POST', currentPath + '?upload=true');
    
    xhr.upload.onprogress = e => {
      if (e.lengthComputable) {
        const pct = Math.round((e.loaded / e.total) * 100);
        fill.style.width = pct + '%';
        status.textContent = `Subiendo ${file.name}... ${pct}%`;
      }
    };
    
    xhr.onload = () => {
      uploaded++;
      status.textContent = `Subidos ${uploaded}/${files.length}`;
      if (uploaded === files.length) {
        setTimeout(() => location.reload(), 500);
      }
    };
    
    xhr.send(formData);
  }
}

function formatSize(bytes) {
  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  let i = 0;
  while (bytes >= 1024 && i < units.length - 1) { bytes /= 1024; i++; }
  return bytes.toFixed(1) + ' ' + units[i];
}

// Load IP & hostname
fetch(baseUrl + '?getip=true')
  .then(r => r.json())
  .then(data => {
    document.getElementById('ip').textContent = data.ip;
    document.getElementById('host').textContent = data.hostname + '.ts.net';
  })
  .catch(() => {
    document.getElementById('ip').textContent = 'N/A';
    document.getElementById('host').textContent = 'N/A';
  });

// Time
document.getElementById('time').textContent = new Date().toLocaleString('es');
</script>
</body>
</html>"""

class FileHandler(http.server.BaseHTTPRequestHandler):
    
    def log_message(self, format, *args):
        """Log coloreado"""
        print(f"\033[36m[{self.log_date_time_string()}]\033[0m {args[0]}")
    
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rel_path = urllib.parse.unquote(parsed.path.lstrip('/'))
        full_path = os.path.join(BASE_DIR, rel_path)
        
        # Get IP + hostname
        if 'getip' in query:
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            data = json.dumps({
                "ip": get_local_ip(),
                "hostname": get_hostname()
            })
            self.wfile.write(data.encode())
            return
        
        # Download directory as ZIP
        if 'download_dir' in query and os.path.isdir(full_path):
            self.send_zip(full_path, rel_path or "files")
            return
        
        # Directory listing
        if os.path.isdir(full_path):
            self.send_html(full_path, rel_path)
        # Download file
        elif os.path.isfile(full_path):
            self.send_file(full_path)
        else:
            self.send_error(404, "Archivo no encontrado")
    
    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        rel_path = urllib.parse.unquote(parsed.path.lstrip('/'))
        full_path = os.path.join(BASE_DIR, rel_path)
        
        if 'upload' in query:
            self.handle_upload(full_path)
        else:
            self.send_error(400, "Bad request")
    
    def handle_upload(self, dest_dir):
        """Recibe archivos subidos"""
        content_type = self.headers['Content-Type']
        if 'multipart/form-data' not in content_type:
            self.send_error(400, "Expected multipart/form-data")
            return
        
        boundary = content_type.split('boundary=')[1].encode()
        content_length = int(self.headers['Content-Length'])
        body = self.rfile.read(content_length)
        
        # Parse multipart manually
        parts = body.split(b'--' + boundary)
        uploaded = []
        
        for part in parts[2:]:  # Skip first empty and last --
            if b'filename="' not in part:
                continue
            header_end = part.find(b'\r\n\r\n')
            if header_end == -1:
                continue
            header = part[:header_end].decode('utf-8', errors='replace')
            data = part[header_end+4:]
            if data.endswith(b'\r\n'):
                data = data[:-2]
            
            # Extract filename
            fname_start = header.find('filename="') + 10
            fname_end = header.find('"', fname_start)
            filename = header[fname_start:fname_end]
            
            if filename:
                filepath = os.path.join(dest_dir, filename)
                os.makedirs(dest_dir, exist_ok=True)
                with open(filepath, 'wb') as f:
                    f.write(data)
                uploaded.append(filename)
                print(f"\033[32m  ✅ Subido: {filename} ({human_size(len(data))})\033[0m")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"uploaded": uploaded}).encode())
    
    def send_html(self, dir_path, rel_path):
        """Genera listing HTML"""
        files = []
        dirs = []
        
        try:
            for entry in sorted(os.listdir(dir_path)):
                full = os.path.join(dir_path, entry)
                is_dir = os.path.isdir(full)
                try:
                    stat = os.stat(full)
                    size = stat.st_size if not is_dir else 0
                    mtime = stat.st_mtime
                except:
                    size = 0
                    mtime = 0
                
                entry_rel = os.path.join(rel_path, entry) if rel_path else entry
                
                if is_dir:
                    dirs.append({
                        'name': entry,
                        'path': entry_rel,
                        'icon': '📁',
                    })
                else:
                    files.append({
                        'name': entry,
                        'path': entry_rel,
                        'size': human_size(size),
                        'raw_size': size,
                        'icon': file_icon(entry),
                        'mtime': time.strftime('%Y-%m-%d %H:%M', time.localtime(mtime)),
                    })
        except PermissionError:
            self.send_error(403, "Sin permisos")
            return
        
        # Build breadcrumb
        bc_html = '<a href="/">🏠 Inicio</a>'
        if rel_path:
            parts = rel_path.split('/')
            path_so_far = ""
            for part in parts:
                path_so_far = path_so_far + "/" + part if path_so_far else part
                bc_html += f' / <a href="/{urllib.parse.quote(path_so_far)}/">{part}</a>'
        
        # Build file list
        list_html = ""
        total_size = 0
        
        for d in dirs:
            list_html += f'''
            <li class="file-item">
              <div class="file-icon">{d['icon']}</div>
              <div class="file-info">
                <div class="file-name"><a href="/{urllib.parse.quote(d['path'])}/">{d['name']}/</a></div>
              </div>
            </li>'''
        
        for f in files:
            total_size += f['raw_size']
            encoded = urllib.parse.quote(f['path'])
            list_html += f'''
            <li class="file-item">
              <div class="file-icon">{f['icon']}</div>
              <div class="file-info">
                <div class="file-name"><a href="/{encoded}?download=true">{f['name']}</a></div>
                <div class="file-meta">{f['size']} &middot; {f['mtime']}</div>
              </div>
              <div class="file-actions">
                <a class="btn btn-primary" href="/{encoded}?download=true">⬇️</a>
                <a class="btn btn-danger" href="/{encoded}?delete=true" onclick="return confirm('Eliminar {f['name']}?')">🗑️</a>
              </div>
            </li>'''
        
        count = len(dirs) + len(files)
        stats_html = f'{count} elementos &middot; {human_size(total_size)} total'
        
        html = HTML_TEMPLATE.replace('id="breadcrumb"></div>', f'id="breadcrumb">{bc_html}</div>')
        html = html.replace('id="fileList"></ul>', f'id="fileList">{list_html}</ul>')
        html = html.replace('id="stats"></div>', f'id="stats">{stats_html}</div>')
        
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_file(self, filepath):
        """Envía archivo para descarga"""
        # Handle delete
        if '?delete=true' in self.path:
            os.remove(filepath)
            print(f"\033[31m  🗑️ Eliminado: {os.path.basename(filepath)}\033[0m")
            parent = os.path.dirname(filepath)
            rel = os.path.relpath(parent, BASE_DIR)
            self.send_response(302)
            self.send_header('Location', '/' + urllib.parse.quote(rel) + '/')
            self.end_headers()
            return
        
        filename = os.path.basename(filepath)
        mime, _ = mimetypes.guess_type(filepath)
        if mime is None:
            mime = 'application/octet-stream'
        
        try:
            size = os.path.getsize(filepath)
            self.send_response(200)
            self.send_header('Content-Type', mime)
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(size))
            self.end_headers()
            
            with open(filepath, 'rb') as f:
                self.wfile.write(f.read())
            
            print(f"\033[33m  ⬇️ Descargado: {filename} ({human_size(size)})\033[0m")
        except Exception as e:
            self.send_error(500, str(e))
    
    def send_zip(self, dir_path, name):
        """Envía directorio como ZIP"""
        import zipfile
        import tempfile
        
        tmp = tempfile.NamedTemporaryFile(suffix='.zip', delete=False)
        try:
            with zipfile.ZipFile(tmp, 'w', zipfile.ZIP_DEFLATED) as zf:
                for root, dirs_list, files_list in os.walk(dir_path):
                    for f in files_list:
                        fp = os.path.join(root, f)
                        arcname = os.path.relpath(fp, os.path.dirname(dir_path))
                        zf.write(fp, arcname)
            
            size = os.path.getsize(tmp.name)
            self.send_response(200)
            self.send_header('Content-Type', 'application/zip')
            self.send_header('Content-Disposition', f'attachment; filename="{name}.zip"')
            self.send_header('Content-Length', str(size))
            self.end_headers()
            
            with open(tmp.name, 'rb') as f:
                self.wfile.write(f.read())
            
            print(f"\033[33m  📦 ZIP enviado: {name}.zip ({human_size(size)})\033[0m")
        finally:
            os.unlink(tmp.name)


def main():
    global BASE_DIR, PORT
    
    parser = argparse.ArgumentParser(description="📁 FileServer - Comparte archivos por red")
    parser.add_argument("directory", nargs="?", default=os.path.expanduser("~/storage"),
                        help="Carpeta a servir (default: ~/storage)")
    parser.add_argument("--port", "-p", type=int, default=8080, help="Puerto (default: 8080)")
    args = parser.parse_args()
    
    BASE_DIR = os.path.abspath(args.directory)
    PORT = args.port
    
    if not os.path.isdir(BASE_DIR):
        print(f"\033[31m❌ Carpeta no encontrada: {BASE_DIR}\033[0m")
        sys.exit(1)
    
    ip = get_local_ip()
    hostname = get_hostname()
    
    print(f"""
\033[36m╔══════════════════════════════════════════════╗
║          📁 FileServer v1.0                   ║
╠══════════════════════════════════════════════╣
║                                              ║
║  🌐 IP:       \033[33mhttp://{ip}:{PORT}\033[36m     
║  🖥️ Hostname: \033[33mhttp://{hostname}.ts.net:{PORT}\033[36m
║  📂 Sirve:    \033[33m{BASE_DIR[:37]}\033[36m
║                                              ║
║  ⚡ Ctrl+C para detener                       ║
╚══════════════════════════════════════════════╝\033[0m
""")
    
    server = http.server.HTTPServer(("0.0.0.0", PORT), FileHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n\033[31m🛑 Servidor detenido.\033[0m")
        server.server_close()


if __name__ == "__main__":
    main()
