#!/data/data/com.termux/files/usr/bin/python3
"""
⚡ SSH-FINDER PRO v2: DETECTOR + GUARDADOR DE CREDENCIALES
- Detecta subredes reales (/24, /16, hotspot y router)
- Escanea puertos SSH comunes: 22, 2222, 8022
- Guarda usuario y contraseña por IP
- Conexión directa con credenciales guardadas
"""

import subprocess
import os
import sys
import re
import json
import getpass

C_CYAN = "\033[1;36m"
C_BLUE = "\033[1;34m"
C_GREEN = "\033[1;32m"
C_YELLOW = "\033[1;33m"
C_MAGENTA = "\033[1;35m"
C_RED = "\033[1;31m"
C_WHITE = "\033[1;37m"
C_DIM = "\033[2;37m"
C_BOLD = "\033[1m"
C_RESET = "\033[0m"

SSH_PORTS = "22,2222,8022"
CREDS_FILE = os.path.expanduser("~/.ssh-finder-creds.json")

def load_creds():
    """Carga credenciales guardadas"""
    if os.path.exists(CREDS_FILE):
        try:
            with open(CREDS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_creds(creds):
    """Guarda credenciales"""
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)
    os.chmod(CREDS_FILE, 0o600)

def get_or_set_creds(ip, port):
    """Obtiene credenciales guardadas o pide al usuario y las guarda"""
    creds = load_creds()
    key = f"{ip}:{port}"

    if key in creds:
        saved = creds[key]
        print(f"\n{C_GREEN}🔑 Credenciales encontradas para {ip}:{port}{C_RESET}")
        print(f"  {C_WHITE}Usuario:{C_RESET} {saved['user']}")
        print(f"  {C_WHITE}Contraseña:{C_RESET} {'*' * len(saved['password'])}")
        use_saved = input(f"\n{C_YELLOW}¿Usar estas credenciales? [S/n]:{C_RESET} ").strip().lower()
        if use_saved in ["", "s", "si", "y", "yes"]:
            return saved["user"], saved["password"]

    # Pedir credenciales nuevas
    print(f"\n{C_CYAN}📝 Configurando credenciales para {ip}:{port}{C_RESET}")
    user = input(f"{C_WHITE}👤 Usuario:{C_RESET} ").strip()
    if not user:
        user = "rootkit"

    try:
        password = getpass.getpass(f"{C_WHITE}🔑 Contraseña:{C_RESET} ")
    except Exception:
        password = input(f"{C_WHITE}🔑 Contraseña (visible):{C_RESET} ").strip()

    save = input(f"{C_YELLOW}¿Guardar credenciales para futuras conexiones? [S/n]:{C_RESET} ").strip().lower()
    if save in ["", "s", "si", "y", "yes"]:
        creds[key] = {"user": user, "password": password}
        save_creds(creds)
        print(f"{C_GREEN}✅ Credenciales guardadas en {CREDS_FILE}{C_RESET}")

    return user, password

def remove_creds(ip, port):
    """Elimina credenciales guardadas"""
    creds = load_creds()
    key = f"{ip}:{port}"
    if key in creds:
        del creds[key]
        save_creds(creds)
        print(f"{C_GREEN}🗑️ Credenciales de {ip}:{port} eliminadas{C_RESET}")
    else:
        print(f"{C_YELLOW}No hay credenciales guardadas para {ip}:{port}{C_RESET}")

def list_creds():
    """Lista todas las credenciales guardadas"""
    creds = load_creds()
    if not creds:
        print(f"{C_YELLOW}No hay credenciales guardadas.{C_RESET}")
        return
    print(f"\n{C_CYAN}🔑 Credenciales Guardadas:{C_RESET}\n")
    for key, val in creds.items():
        print(f"  {C_WHITE}{key}{C_RESET} → {C_GREEN}{val['user']}{C_RESET} / {'*' * len(val['password'])}")

def get_all_subnets():
    """Detecta las subredes reales"""
    subnets = []
    try:
        res = subprocess.run(["ip", "-o", "-4", "addr", "show"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "lo" not in line and "docker" not in line:
                match = re.search(r'inet\s+(\d+\.\d+\.\d+\.\d+)/(\d+)', line)
                if match:
                    ip = match.group(1)
                    subnet = ".".join(ip.split(".")[:3]) + ".0/24"
                    if subnet not in subnets:
                        subnets.append(subnet)
    except Exception:
        pass

    try:
        res = subprocess.run(["ip", "route", "show"], capture_output=True, text=True)
        for line in res.stdout.splitlines():
            if "default via" in line:
                match = re.search(r'default via (\d+\.\d+\.\d+\.\d+)', line)
                if match:
                    gw = match.group(1)
                    subnet = ".".join(gw.split(".")[:3]) + ".0/24"
                    if subnet not in subnets:
                        subnets.append(subnet)
    except Exception:
        pass

    common_subnets = ["192.168.40.0/24", "192.168.1.0/24", "192.168.0.0/24", "192.168.43.0/24"]
    for s in common_subnets:
        if s not in subnets:
            subnets.append(s)

    return subnets

def scan_all_targets():
    subnets = get_all_subnets()
    print(f"\n{C_BLUE}🔍 Escaneando subredes buscando servidores SSH (Puertos: {SSH_PORTS})...{C_RESET}")
    for s in subnets[:2]:
        print(f"  {C_DIM}• Rango: {s}{C_RESET}")

    targets_arg = " ".join(subnets[:2])
    cmd = f"nmap -Pn -p {SSH_PORTS} --open -T4 --min-rate 400 {targets_arg}"
    try:
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=25)
        output = res.stdout
    except Exception:
        output = ""

    servers = []
    current_ip = None
    current_host = "PC / Host"

    for line in output.splitlines():
        if "Nmap scan report for" in line:
            parts = line.replace("Nmap scan report for", "").strip().split()
            if len(parts) == 1:
                current_ip = parts[0].strip("()")
                current_host = "PC / Dispositivo"
            elif len(parts) >= 2:
                current_host = parts[0]
                current_ip = parts[1].strip("()")
        elif "/tcp" in line and "open" in line and current_ip:
            port_num = int(line.split("/")[0].strip())
            port_type = "PC Linux / Servidor" if port_num in [22, 2222] else "Termux Android"
            servers.append({
                "ip": current_ip,
                "port": port_num,
                "hostname": current_host,
                "type": port_type
            })

    return servers

def connect_ssh(ip, port, user, password):
    """Conecta por SSH usando sshpass si hay contraseña"""
    print(f"\n{C_BLUE}🔗 Conectando a {user}@{ip}:{port}...{C_RESET}\n")
    if password:
        # Usar sshpass si está disponible
        cmd = f"sshpass -p '{password}' ssh -o StrictHostKeyChecking=no"
        if port != 22:
            cmd += f" -p {port}"
        cmd += f" {user}@{ip}"
        os.system(cmd)
    else:
        if port == 22:
            os.system(f"ssh {user}@{ip}")
        else:
            os.system(f"ssh -p {port} {user}@{ip}")

def main():
    # Modo CLI
    if len(sys.argv) >= 2:
        cmd = sys.argv[1]

        if cmd == "creds" or cmd == "credenciales":
            list_creds()
            return
        elif cmd == "remove" or cmd == "rm":
            if len(sys.argv) >= 4:
                remove_creds(sys.argv[2], int(sys.argv[3]))
            else:
                print(f"{C_RED}Uso: ssh-find rm <ip> <puerto>{C_RESET}")
            return
        elif cmd == "help":
            print(f"""
{C_CYAN}⚡ SSH-FINDER PRO v2{C_RESET}

{C_WHITE}Modo interactivo:{C_RESET}
  ssh-find              Escanea y conecta

{C_WHITE}Modo CLI:{C_RESET}
  ssh-find creds        Ver credenciales guardadas
  ssh-find rm IP PUERTO Eliminar credenciales
  ssh-find help         Esta ayuda
""")
            return

    # Banner
    print(f"{C_CYAN}╭──────────────────────────────────────────────────────────────╮{C_RESET}")
    print(f"{C_CYAN}│     ⚡  SSH-FINDER PRO v2 + CREDENCIALES                     │{C_RESET}")
    print(f"{C_CYAN}╰──────────────────────────────────────────────────────────────╯{C_RESET}")

    servers = scan_all_targets()

    if not servers:
        print(f"\n{C_RED}❌ No se encontraron servidores SSH abiertos.{C_RESET}")
        print(f"{C_YELLOW}💡 Tip: Revisa que tu PC esté conectada al mismo Wi-Fi.{C_RESET}\n")
        sys.exit(0)

    print(f"\n{C_GREEN}🖥️  Servidores SSH Encontrados:{C_RESET}\n")

    for idx, s in enumerate(servers, 1):
        creds = load_creds()
        key = f"{s['ip']}:{s['port']}"
        has_creds = f" {C_GREEN}(guardado){C_RESET}" if key in creds else ""
        print(f"  {C_CYAN}[{idx}]{C_RESET} {C_BOLD}{C_GREEN}IP:{C_RESET} {C_WHITE}{s['ip']}{C_RESET} {C_YELLOW}(Puerto {s['port']}){C_RESET} | {C_WHITE}{s['type']}{C_RESET} ({s['hostname']}){has_creds}")

    if len(servers) == 1:
        target = servers[0]
        print(f"\n{C_GREEN}👉 Se detectó tu PC automáticamente en:{C_RESET} {C_BOLD}{C_YELLOW}{target['ip']}:{target['port']}{C_RESET}")
        choice = input(f"\n{C_WHITE}¿Deseas conectarte ahora? [S/n]:{C_RESET} ").strip().lower()
        if choice not in ["", "s", "si", "y", "yes"]:
            sys.exit(0)
    else:
        choice = input(f"\n{C_GREEN}👉 Selecciona tu PC [1-{len(servers)} o Enter para salir]:{C_RESET} ").strip()
        if not choice.isdigit() or not (1 <= int(choice) <= len(servers)):
            sys.exit(0)
        target = servers[int(choice) - 1]

    user, password = get_or_set_creds(target["ip"], target["port"])
    connect_ssh(target["ip"], target["port"], user, password)

if __name__ == "__main__":
    main()
