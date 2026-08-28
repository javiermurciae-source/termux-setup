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

# Tailscale - la app maneja todo, no necesitamos daemon en Termux
alias tsup='echo "Abre http://cachyos-x8664:8081 en tu navegador"'
alias tsdown='echo "Cierra la app Tailscale desde la notificacion"'
alias tsstatus='curl -s --connect-timeout 3 http://cachyos-x8664:8081/ >/dev/null 2>&1 && echo "PC: Online" || echo "PC: Offline - abre la app Tailscale"'
alias tspc='curl -s --connect-timeout 3 http://cachyos-x8664:8081/ >/dev/null 2>&1 && echo "Abre http://cachyos-x8664:8081" || echo "PC offline"'

# FileBrowser - gestor de archivos web
alias fb='screen -dmS filebrowser filebrowser -r ~/storage -a 0.0.0.0 -p 8081 -d ~/.filebrowser.db --noauth; sleep 1; echo "http://tailscale-termux:8081"'
alias fb-stop='screen -S filebrowser -X quit 2>/dev/null; pkill filebrowser 2>/dev/null; echo "stopped"'
alias fb-pc='tailscale-cli ssh rootkit@cachyos-x8664 "bash -c \"nohup filebrowser -r /home/rootkit -a 0.0.0.0 -p 8081 -d ~/.filebrowser.db --noauth >/dev/null 2>&1 &\"" 2>/dev/null; echo "http://cachyos-x8664:8081"'

# Sincronizador Maestro
alias sync-setup='curl -sL https://raw.githubusercontent.com/javiermurciae-source/termux-setup/main/setup-todo -o ~/.setup-todo.sh && rm -f ~/.core_setup_done && bash ~/.setup-todo.sh </dev/tty>'

set -gx PATH $HOME/.local/bin $PATH
set -gx JAVA_HOME $PREFIX




