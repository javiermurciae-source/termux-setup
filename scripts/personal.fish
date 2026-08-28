# === Personal ===
alias ll='ls -la'
alias ..='cd ..'
alias cls='clear'
alias update='dpkg --configure -a 2>/dev/null; pkg update -y && pkg upgrade -y'
alias fix-media='fix-media'

# Scripts
alias horario='bash ~/horario.sh'
alias tren='sl'
alias gif='bash ~/gif-selector.sh'

# Root & ADB
alias s='sudo'
alias adbs='adb shell'
alias adbd='adb devices'

# Herramientas
alias codc='bash ~/verificar-cod.sh'
alias ssh-find='ssh-find'
alias speed='speedtest-go'
alias transfile='transfile'
alias sploit='searchsploit'
alias dlab='doclab'

# Power Tools
alias top='htop'
alias disco='ncdu'
alias pinga='mtr'
alias tracer='traceroute'
alias session='screen'
alias yam='yq'
alias json='jq'
alias info='fastfetch'

# Tailscale (app maneja todo)
alias tsstatus='curl -s --connect-timeout 3 http://cachyos-x8664:8081/ >/dev/null 2>&1 && echo "PC: Online" || echo "PC: Offline"'
alias tspc='ssh -o ConnectTimeout=5 rootkit@cachyos-x8664'

# FileBrowser
alias fb='screen -dmS filebrowser filebrowser -r ~/storage -a 0.0.0.0 -p 8081 -d ~/.filebrowser.db --noauth; sleep 1; echo "http://tailscale-termux:8081"'
alias fb-stop='screen -S filebrowser -X quit 2>/dev/null; pkill filebrowser 2>/dev/null; echo "stopped"'
alias fb-pc='tailscale-cli ssh rootkit@cachyos-x8664 "bash -c \"nohup filebrowser -r /home/rootkit -a 0.0.0.0 -p 8081 -d ~/.filebrowser.db --noauth >/dev/null 2>&1 &\"" 2>/dev/null; echo "http://cachyos-x8664:8081"'

# Sync
alias sync-setup='curl -sL https://raw.githubusercontent.com/javiermurciae-source/termux-setup/main/setup-todo -o ~/.setup-todo.sh && rm -f ~/.core_setup_done && bash ~/.setup-todo.sh </dev/tty>'

set -gx PATH $HOME/.local/bin $PATH
set -gx JAVA_HOME $PREFIX

# Kitten (Kitty features)
alias kicat='kitten icat'
alias kssh='kitten ssh rootkit@cachyos-x8664'
alias ktransfer='kitten transfer'
alias kdiff='kitten diff'
alias kclip='kitten clipboard'
alias knotify='kitten notify'
alias btop='su -c "/data/data/com.termux/files/usr/bin/btop"'
