# === Configuración personal ===
alias ll='ls -la'
alias ..='cd ..'
alias cls='clear'
alias update='dpkg --configure -a 2>/dev/null
    pkg update -y && pkg upgrade -y'
alias horario='bash ~/horario.sh'
alias tren='sl'
alias gif='bash ~/gif-selector.sh'
alias fix-media='fix-media'

# Root & ADB
alias s='sudo'
alias adbs='adb shell'
alias adbd='adb devices'
alias adbw='adb tcpip 5555 && adb connect'

# Herramientas de Productividad y Dev
alias mail='readmail'
alias readmail='readmail'
alias inbox='inbox'
alias codc='bash ~/verificar-cod.sh'
alias netscan='netscan'
alias lanscan='netscan'
alias ssh-find='ssh-find'
alias findpc='ssh-find'
alias speed='speedtest-go'
alias speedtest='speedtest-go'
alias transfile='transfile'
alias pasar='transfile'
alias searchsploit='searchsploit'
alias sploit='searchsploit'

# Document Lab
alias dlab='doclab'

# Power Tools - Monitoreo
alias top='htop'
alias monitor='htop'
alias disco='ncdu'
alias disk='ncdu'

# Power Tools - Red
alias pinga='mtr'
alias tracer='traceroute'
alias netdiag='mtr'

# Power Tools - Terminal
alias session='screen'
alias ssession='screen -r'

# Power Tools - Procesamiento
alias yam='yq'
alias json='jq'

# Power Tools - Sistema
alias sysinfo='fastfetch'
alias info='fastfetch'

# Tailscale on-demand
alias tsup='rm -f ~/.tailscale/tailscaled.sock; screen -dmS tailscale bash -c "tailscaled --statedir=$HOME/.tailscale --socket=$HOME/.tailscale/tailscaled.sock --tun=userspace-networking --socks5-server=localhost:1055"; sleep 8; tailscale-cli status 2>/dev/null | head -3'
alias tsdown='killall -9 tailscaled 2>/dev/null; rm -f ~/.tailscale/tailscaled.sock; screen -S tailscale -X quit 2>/dev/null; echo "Tailscale apagado"'
alias tsstatus='tailscale-cli status 2>/dev/null || echo "Tailscale apagado. Usa tsup para encender."'
alias tspc='tailscale-cli ssh rootkit@cachyos-x8664'

# FileServer - Compartir archivos por red
alias fs='python3 ~/storage/termux-setup/scripts/fileserver-tui.py'
alias fs-down='python3 ~/storage/termux-setup/scripts/fileserver-tui.py ~/storage/downloads'
alias fs-share='python3 ~/storage/termux-setup/scripts/fileserver-tui.py ~'
alias fileserver='python3 ~/storage/termux-setup/scripts/fileserver.py'
alias fileserver-web='python3 ~/storage/termux-setup/scripts/fileserver.py ~'

# Sincronizador Maestro
alias sync-setup='curl -sL https://raw.githubusercontent.com/javiermurciae-source/termux-setup/main/setup-todo -o ~/.setup-todo.sh && rm -f ~/.core_setup_done && bash ~/.setup-todo.sh </dev/tty>'

set -gx PATH $HOME/.local/bin $PATH
set -gx JAVA_HOME $PREFIX
