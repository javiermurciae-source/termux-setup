# Termux Launcher — launcher-owned fish config. setup-launcher replaces this
# file on every run (after a timestamped .bak), so keep only what the launcher
# integration itself needs here: PATH, the wallpaper Material palette and its
# per-prompt refresh, the clear/cursor helpers, and the Oh My Posh prompt.
#
# YOUR OWN SETTINGS GO IN ~/.config/fish/conf.d/personal.fish (installed once
# from the conf.d-personal.fish example and never overwritten). Editor, aliases,
# and the ls/cd helpers all live there. Note fish loads conf.d/*.fish BEFORE
# this file.

set -g fish_greeting ""

# PATH consolidado — un solo fork
set -l _paths "$HOME/.local/bin" "$HOME/.termux/bin"
test -d "$HOME/.nix-profile/bin"; and set _paths "$HOME/.nix-profile/bin" $PATH
test -d /nix; and set -a _paths /bin
fish_add_path --prepend $_paths
set -e _paths

# TMPDIR solo si no existe
set -gx TMPDIR "$HOME/.tmp"
test -d "$TMPDIR"; or mkdir -p "$TMPDIR"

set -q COLORTERM; or set -gx COLORTERM truecolor

# --- Material colors ---
function __load_termux_material_colors
    set -l f "$HOME/.termux/material-colors.sh"
    test -r "$f"; and source "$f"; and return
    set -f "$HOME/.termux/material-colors.properties"
    test -r "$f"; or return

    while read -l line
        string match -qr '^\s*(#|$)' -- "$line"; and continue
        set -l kv (string split -m 1 '=' -- (string trim -- "$line"))
        test (count $kv) -eq 2; or continue
        set -gx TERMUX_MATERIAL_(string upper -- $kv[1] | tr '-' '_') $kv[2]
    end < "$f"
end

__load_termux_material_colors

set -g __termux_material_colors_signature ""
function __refresh_termux_material_colors --on-event fish_prompt
    set -l f "$HOME/.termux/material-colors.sh"
    test -r "$f"; or set f "$HOME/.termux/material-colors.properties"
    test -r "$f"; or return

    set -l sig (command stat -c '%Y:%s' "$f" 2>/dev/null)
    test -n "$sig"; or return
    test "$sig" = "$__termux_material_colors_signature"; and return

    __load_termux_material_colors
    set -g __termux_material_colors_signature "$sig"
end

# Fallback palette — helper function + single call
function __material_defaults
    for i in (seq 1 2 (count $argv))
        set -q $argv[$i]; or set -gx $argv[$i] $argv[(math $i + 1)]
    end
end

__material_defaults \
    TERMUX_MATERIAL_ERROR "#F2B8B5" \
    TERMUX_MATERIAL_ERROR_CONTAINER "#8C1D18" \
    TERMUX_MATERIAL_ON_PRIMARY "#003826" \
    TERMUX_MATERIAL_ON_SECONDARY "#1E3529" \
    TERMUX_MATERIAL_ON_SURFACE "#DEE4DE" \
    TERMUX_MATERIAL_ON_SURFACE_VARIANT "#C0C9C0" \
    TERMUX_MATERIAL_PRIMARY "#8CD5B3" \
    TERMUX_MATERIAL_SECONDARY "#B3CCBE" \
    TERMUX_MATERIAL_SURFACE "#0F1512" \
    TERMUX_MATERIAL_SURFACE_CONTAINER_HIGHEST "#303632" \
    TERMUX_MATERIAL_SURFACE_VARIANT "#404943" \
    TERMUX_MATERIAL_TERTIARY "#A5CCDF" \
    TERMUX_MATERIAL_TERTIARY_CONTAINER "#234C5E" \
    TERMUX_MATERIAL_ON_TERTIARY_CONTAINER "#C1E8FB" \
    TERMUX_MATERIAL_ON_ERROR_CONTAINER "#F9DEDC"

functions -e __material_defaults

if status is-interactive
    # Neovim chooser hint (once)
    set -l _cfg (test -n "$XDG_CONFIG_HOME"; and echo "$XDG_CONFIG_HOME"; or echo "$HOME/.config")
    if type -q setup-nvim; and not test -e "$_cfg/nvim"; and not test -e "$_cfg/.setup-nvim-hinted"
        echo "Neovim has no config yet — run 'setup-nvim' to pick one."
        touch "$_cfg/.setup-nvim-hinted"
    end

    # Oh My Posh
    if type -q oh-my-posh
        set -l _omp "$HOME/.config/ohmyposh/aliens-material.omp.json"
        test -f "$_omp"; and oh-my-posh --config "$_omp" init fish | source
    end
end
