#!/bin/bash
set -eu

extension_name=phpstorm-nautilus.py
extension_dir="${XDG_DATA_HOME:-$HOME/.local/share}/nautilus-python/extensions"
installed="$extension_dir/$extension_name"
source_url="https://raw.githubusercontent.com/terciotales/phpstorm-nautilus/main/$extension_name"

fail() {
    echo "$*" >&2
    exit 1
}

if (( $# > 1 )); then
    fail "Usage: bash install.sh [--configure | --remove]"
fi
case "${1:-}" in
    --configure|--remove)
        [[ -f "$installed" ]] || fail "Install the extension first with bash install.sh."
        exec /usr/bin/python3 "$installed" "$1"
        ;;
    --help|-h)
        echo "Usage: bash install.sh [--configure | --remove]"
        exit 0
        ;;
    '') ;;
    *) fail "Usage: bash install.sh [--configure | --remove]" ;;
esac

[[ -x /usr/bin/python3 ]] || fail "Install your distribution's Python 3 to run this installer."

work_dir=$(mktemp -d)
staged="$work_dir/$extension_name"
pending_selection="$work_dir/shortcuts.json"
replacement=''
cleanup() {
    if [[ -n "$replacement" ]]; then
        rm -f -- "$replacement"
    fi
    rm -f -- "$staged" "$pending_selection"
    rmdir -- "$work_dir"
}
trap cleanup EXIT
trap 'exit 1' HUP INT TERM

script_path=${BASH_SOURCE[0]:-}
if [[ -n "$script_path" && -f "$(dirname -- "$script_path")/$extension_name" ]]; then
    cp -- "$(dirname -- "$script_path")/$extension_name" "$staged"
else
    wget -nv -O "$staged" "$source_url" || fail "Could not download the extension."
fi

[[ -s "$staged" ]] || fail "The extension file is empty."
/usr/bin/python3 -c 'import sys; compile(open(sys.argv[1], "rb").read(), sys.argv[2], "exec")' "$staged" "$extension_name" ||
    fail "The extension file is invalid."

select_shortcuts() {
    local status=0
    /usr/bin/python3 "$staged" --stage-selection "$pending_selection" || status=$?
    if [[ "$status" == 2 ]]; then
        echo "Installation canceled."
        exit 2
    fi
    [[ "$status" == 0 && -f "$pending_selection" ]] || fail "Could not prepare the shortcut selection."
}

if [[ -t 0 ]]; then
    select_shortcuts
elif ( : < /dev/tty ) 2>/dev/null; then
    select_shortcuts < /dev/tty
else
    echo "No interactive terminal. Run bash install.sh --configure to select shortcuts."
fi

if command -v pacman >/dev/null 2>&1; then
    pacman -Q nautilus-python zenity >/dev/null 2>&1 ||
        sudo pacman -S --needed --noconfirm nautilus-python zenity ||
        fail "Could not install nautilus-python and zenity."
elif command -v apt-get >/dev/null 2>&1; then
    if [[ $(dpkg-query -W -f='${Status}\n' python3-nautilus zenity 2>/dev/null || true) != $'install ok installed\ninstall ok installed' ]]; then
        sudo apt-get install -y python3-nautilus zenity ||
            fail "Could not install python3-nautilus and zenity. Check that the packages are available in your APT repositories."
    fi
elif command -v dnf >/dev/null 2>&1; then
    rpm -q nautilus-python zenity >/dev/null 2>&1 ||
        sudo dnf install -y nautilus-python zenity ||
        fail "Could not install nautilus-python and zenity."
else
    fail "Unsupported package manager. Install the Nautilus Python bindings and Zenity, then follow the manual installation instructions."
fi

command -v nautilus >/dev/null 2>&1 || fail "Nautilus is required."

mkdir -p -- "$extension_dir"
replacement=$(mktemp "$extension_dir/.phpstorm-nautilus.XXXXXX")
cp -- "$staged" "$replacement"
mv -fT -- "$replacement" "$installed"
replacement=''
rm -f -- "$extension_dir/PHPStormExtension.py"

if [[ -f "$pending_selection" ]]; then
    /usr/bin/python3 "$staged" --apply-selection "$pending_selection"
    echo "Shortcuts saved."
fi

echo "Extension installed."
if [[ -t 0 ]]; then
    /usr/bin/python3 "$staged" --restart-nautilus
elif ( : < /dev/tty ) 2>/dev/null; then
    /usr/bin/python3 "$staged" --restart-nautilus < /dev/tty
else
    /usr/bin/python3 "$staged" --restart-nautilus
fi
