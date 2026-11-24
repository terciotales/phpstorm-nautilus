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
staged=$(mktemp "$extension_dir/.phpstorm-nautilus.XXXXXX")
trap 'rm -f -- "$staged"' EXIT
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

mv -fT -- "$staged" "$installed"
rm -f -- "$extension_dir/PHPStormExtension.py"

echo "Extension installed. Run nautilus -q, then reopen Files."
