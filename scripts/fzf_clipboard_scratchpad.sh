#!/data/data/com.termux/files/usr/bin/bash
# Script de Portapapeles FZF Flotante (Gboard Root Extractor)

su -c "cat /data/data/com.google.android.inputmethod.latin/databases/gboard_clipboard.db" > ~/.termux/tmp_clip.db 2>/dev/null
selected=$(sqlite3 ~/.termux/tmp_clip.db "SELECT text FROM clips ORDER BY timestamp DESC;" 2>/dev/null | fzf --height 50% --reverse --border=rounded --prompt="📋 Portapapeles: ")
if [ -n "$selected" ]; then
    echo -n "$selected" | termux-clipboard-set 2>/dev/null || true
    echo "$selected"
fi

