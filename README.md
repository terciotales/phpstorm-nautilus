# phpstorm-nautilus

Adds shortcuts for your chosen IDEs to the Nautilus context menu. Right-click files or folders with local paths, or right-click the window background to open the current folder.

## Prerequisites

- Your distribution's Python 3 to run the installer. The extension requires Nautilus with Python bindings (API 3.0, 4.0, or 4.1) and Zenity.
- At least one installed IDE to create a shortcut.

## Installation

On Ubuntu, Arch Linux, or Fedora, clone the repository and run the installer as your user:

```sh
git clone https://github.com/terciotales/phpstorm-nautilus.git
cd phpstorm-nautilus
bash install.sh
```

On Ubuntu, `python3-nautilus` is in the `universe` repository. The installer uses `sudo` if it needs to install packages.

The installer applies changes after you confirm the selection with **Enter**. **Esc** or **Q** cancels installation and preserves any previous version and shortcuts.

After installation, Nautilus restarts automatically. If it has open windows or the installer cannot check them, it asks before closing any windows or tabs. Press **Y** to restart or **Enter** to postpone. If you postpone, the extension loads the next time Nautilus starts.

On other distributions, install the Nautilus Python bindings and Zenity through your package manager. Copy `phpstorm-nautilus.py` to `${XDG_DATA_HOME:-$HOME/.local/share}/nautilus-python/extensions/` and restart Nautilus.

## Managing shortcuts

The installer opens the shortcut language selector first, then shows the detected IDEs. Use **↑/↓** to navigate, **Space** to toggle a shortcut, **Enter** to confirm, and **Esc** or **Q** to cancel. Terminals without support for the interactive screen use numbered choices. PhpStorm is selected on first setup when detected.

Detection covers OpenIDEA, IntelliJ IDEA, PhpStorm, PyCharm, WebStorm, CLion, GoLand, Rider, RubyMine, DataGrip, DataSpell, RustRover, Aqua, Android Studio, Visual Studio Code, and VSCodium. It looks for launchers on `PATH`, in `~/.local/bin`, and in known Toolbox, Snap, and `/opt` locations. It also checks `~/Applications` for the OpenIDEA AppImage. Enter `a` to add an IDE by name and full executable path if it does not appear.

```sh
bash install.sh --configure  # Detect IDEs again and edit the selection
bash install.sh --remove     # Mark shortcuts to remove
```

These commands update the menu without uninstalling any IDEs. Reinstalling preserves existing selections. If a selected IDE becomes unavailable, its shortcut is hidden until the executable is available again. The selection is stored in `${XDG_CONFIG_HOME:-$HOME/.config}/phpstorm-nautilus/shortcuts.json`. When installing without an interactive terminal, run `--configure` afterwards to select shortcuts.

### Shortcut language

During installation or when running `bash install.sh --configure`, preview and select the language for all IDE shortcut labels in Nautilus. Press **Enter** to continue to the IDE list, then press **Enter** again to save both selections. The selector highlights the saved language when you return.

English is the default. Other options are Brazilian Portuguese, Spanish, French, German, and Italian. The terminal interface and installer messages are in English.

### Custom PhpStorm launcher

To prioritize a PhpStorm executable without creating a second shortcut, set `PHPSTORM_LAUNCHER` to its full path in your graphical session environment. For example, in a GNOME session that loads `~/.config/environment.d/`, create `~/.config/environment.d/90-phpstorm.conf` containing:

```ini
PHPSTORM_LAUNCHER=/opt/PhpStorm/bin/phpstorm.sh
```

Log out and back in to apply the variable.

## Uninstallation

```sh
rm -f -- "${XDG_DATA_HOME:-$HOME/.local/share}/nautilus-python/extensions/phpstorm-nautilus.py"
nautilus -q
```

Reopen Files.
