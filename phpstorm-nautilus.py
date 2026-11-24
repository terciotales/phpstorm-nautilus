# Nautilus IDE shortcuts. Released to the public domain.

import json
import os
from pathlib import Path
import shutil
from subprocess import DEVNULL, Popen, SubprocessError, run
import sys
from tempfile import NamedTemporaryFile
from time import monotonic, sleep
from uuid import uuid4


NEWWINDOW = False
DEFAULT_LANGUAGE = 'en'
MENU_LANGUAGES = {
    'en': ('English', 'Open in {ide}'),
    'pt-BR': ('Portuguese (Brazil)', 'Abrir no {ide}'),
    'es': ('Spanish', 'Abrir en {ide}'),
    'fr': ('French', 'Ouvrir dans {ide}'),
    'de': ('German', 'Öffnen mit {ide}'),
    'it': ('Italian', 'Apri in {ide}'),
}

# The first launcher is also the executable name used inside standalone installs.
IDES = {
    'phpstorm': ('PhpStorm', ('phpstorm',)),
    'idea': ('IntelliJ IDEA', ('idea', 'intellij-idea', 'intellij-idea-ultimate', 'intellij-idea-community')),
    'pycharm': ('PyCharm', ('pycharm', 'pycharm-professional', 'pycharm-community')),
    'webstorm': ('WebStorm', ('webstorm',)),
    'clion': ('CLion', ('clion',)),
    'goland': ('GoLand', ('goland',)),
    'rider': ('Rider', ('rider',)),
    'rubymine': ('RubyMine', ('rubymine',)),
    'datagrip': ('DataGrip', ('datagrip',)),
    'dataspell': ('DataSpell', ('dataspell',)),
    'rustrover': ('RustRover', ('rustrover',)),
    'aqua': ('Aqua', ('aqua',)),
    'studio': ('Android Studio', ('studio', 'android-studio')),
    'openidea': ('OpenIDEA', ('openidea',)),
    'code': ('Visual Studio Code', ('code',)),
    'codium': ('VSCodium', ('codium',)),
}


def config_path():
    base = os.environ.get('XDG_CONFIG_HOME') or Path.home() / '.config'
    return Path(base) / 'phpstorm-nautilus' / 'shortcuts.json'


def read_settings(path=None):
    try:
        data = json.loads((path or config_path()).read_text(encoding='utf-8'))
    except FileNotFoundError:
        if path is not None:
            raise
        return {'phpstorm': ('PhpStorm', '')}, DEFAULT_LANGUAGE

    # Older versions stored the shortcuts directly at the root.
    language = DEFAULT_LANGUAGE
    shortcuts = data
    if isinstance(data, dict) and 'shortcuts' in data:
        shortcuts = data['shortcuts']
        language = data.get('language', DEFAULT_LANGUAGE)

    if not isinstance(shortcuts, dict) or any(
        not isinstance(entry, list) or len(entry) != 2
        or not all(isinstance(value, str) for value in entry)
        for entry in shortcuts.values()
    ):
        raise ValueError('Invalid shortcut configuration format.')
    if not isinstance(language, str) or language not in MENU_LANGUAGES:
        language = DEFAULT_LANGUAGE
    return shortcuts, language


def save_settings(shortcuts, language, path=None):
    path = path or config_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(
        mode='w', dir=path.parent, encoding='utf-8', delete=False,
    ) as staged:
        try:
            json.dump({'language': language, 'shortcuts': shortcuts}, staged, ensure_ascii=False, indent=2)
            staged.write('\n')
            staged.close()
            os.replace(staged.name, path)
        finally:
            Path(staged.name).unlink(missing_ok=True)


def launcher_candidates(ide_id):
    if ide_id not in IDES:
        return

    _, aliases = IDES[ide_id]
    home = Path.home()
    toolbox = home / '.local/share/JetBrains/Toolbox'
    for alias in aliases:
        yield alias
        yield f'{alias}.sh'
        yield home / '.local/bin' / alias
        yield toolbox / 'scripts' / alias
        yield Path('/snap/bin') / alias

    names = ('idea-IU', 'idea-IC', *aliases) if ide_id == 'idea' else aliases
    for root in (toolbox / 'apps', Path('/opt')):
        for name in names:
            directories = [root / name, *sorted(root.glob(f'{name}-*'), reverse=True)]
            for directory in directories:
                yield directory / 'bin' / ide_id
                yield directory / 'bin' / f'{ide_id}.sh'

    if ide_id == 'openidea':
        yield from sorted((home / 'Applications').glob('OpenIDEA*.AppImage'), reverse=True)


def find_launcher(ide_id, saved_path=''):
    if ide_id == 'phpstorm':
        override = os.environ.get('PHPSTORM_LAUNCHER')
        if override:
            launcher = shutil.which(os.path.expanduser(override))
            if launcher:
                return os.path.abspath(launcher)

    # A saved absolute path also works when the desktop and terminal have different PATHs.
    if os.path.isabs(saved_path) and shutil.which(saved_path):
        return saved_path
    for candidate in launcher_candidates(ide_id):
        launcher = shutil.which(str(candidate))
        if launcher:
            return os.path.abspath(launcher)
    return None


def add_custom_shortcut(choices, marked, label, path):
    label = label.strip()
    path = os.path.expanduser(path.strip())
    if not label or not os.path.isabs(path) or not shutil.which(path):
        return False
    ide_id = f'custom-{uuid4().hex}'
    choices[ide_id] = (label, path)
    marked.add(ide_id)
    return True


def shortcut_label(ide_id, choices):
    label, path = choices[ide_id]
    return label if find_launcher(ide_id, path) else f'{label} (executable unavailable)'


def write_terminal_line(screen, row, text, style=0):
    height, width = screen.getmaxyx()
    if row < height and width > 1:
        screen.addnstr(row, 0, text, width - 1, style)


def move_terminal_cursor(key, cursor, size):
    if key == curses.KEY_UP:
        return max(0, cursor - 1)
    if key == curses.KEY_DOWN:
        return min(size - 1, cursor + 1)
    if key == curses.KEY_HOME:
        return 0
    if key == curses.KEY_END:
        return size - 1
    return cursor


def language_previews():
    name_width = max(len(name) for name, _ in MENU_LANGUAGES.values())
    return {
        code: f'{name:<{name_width}}  |  {template.format(ide="PhpStorm")}'
        for code, (name, template) in MENU_LANGUAGES.items()
    }


def pick_language_terminal(screen, language):
    previews = language_previews()
    codes = list(previews)
    row_width = max(map(len, previews.values()))
    cursor = codes.index(language)
    first = 0
    while True:
        height, _ = screen.getmaxyx()
        page_rows = max(1, height - 4)
        first = max(cursor - page_rows + 1, min(first, cursor))
        screen.erase()
        write_terminal_line(screen, 0, '1/2  Choose Nautilus shortcut language', curses.A_BOLD)
        write_terminal_line(screen, 1, '↑/↓ Navigate   Enter Continue   Esc/Q Cancel')
        for row, code in enumerate(codes[first:first + page_rows], first):
            selected = '*' if code == language else ' '
            focus = row == cursor
            write_terminal_line(
                screen, row - first + 3,
                f'{selected} {previews[code]:<{row_width}}',
                curses.A_REVERSE if focus else curses.A_NORMAL,
            )
        screen.refresh()

        key = screen.get_wch()
        if key in ('\n', '\r', curses.KEY_ENTER):
            return codes[cursor]
        if key in ('q', 'Q', '\x1b'):
            return None
        cursor = move_terminal_cursor(key, cursor, len(codes))


def read_terminal_field(screen, title, prompt):
    value = ''
    while True:
        _, width = screen.getmaxyx()
        screen.erase()
        write_terminal_line(screen, 0, title, curses.A_BOLD)
        write_terminal_line(screen, 2, prompt)
        write_terminal_line(screen, 3, '> ' + value[-max(1, width - 4):] + '_')
        write_terminal_line(screen, 5, 'Enter Confirm   Esc Back', curses.A_DIM)
        screen.refresh()

        key = screen.get_wch()
        if key in ('\n', '\r', curses.KEY_ENTER):
            return value
        if key == '\x1b':
            return None
        if key in ('\b', '\x7f', curses.KEY_BACKSPACE):
            value = value[:-1]
        elif isinstance(key, str) and key.isprintable():
            value += key


def pick_shortcuts_terminal(screen, choices, marked, remove, language):
    try:
        curses.curs_set(0)
    except curses.error:
        pass

    if not remove:
        language = pick_language_terminal(screen, language)
        if language is None:
            return None

    title = 'Remove Nautilus shortcuts' if remove else '2/2  Choose Nautilus shortcuts'
    cursor = first = 0
    error = ''
    while True:
        ids = list(choices)
        height, _ = screen.getmaxyx()
        page_rows = max(1, height - 6)
        first = max(cursor - page_rows + 1, min(first, cursor))
        screen.erase()
        write_terminal_line(screen, 0, title, curses.A_BOLD)
        write_terminal_line(screen, 1, '↑/↓ Navigate   Space Toggle selection')
        help_line = 'Enter Remove   Esc/Q Cancel' if remove else 'Enter Save   Esc/Q Cancel'
        write_terminal_line(screen, 2, help_line)
        if not remove:
            write_terminal_line(screen, 3, f'A Add IDE   Language: {MENU_LANGUAGES[language][0]}')
        if not ids:
            write_terminal_line(screen, 4, 'No IDEs detected. Press A to add one.')
        for row, ide_id in enumerate(ids[first:first + page_rows], first):
            focus = row == cursor
            check = 'x' if ide_id in marked else ' '
            prefix = '>' if focus else ' '
            write_terminal_line(
                screen, row - first + 4,
                f'{prefix} [{check}] {shortcut_label(ide_id, choices)}',
                curses.A_REVERSE if focus else curses.A_NORMAL,
            )
        if height >= 7:
            position = f'  |  {cursor + 1}/{len(ids)}' if ids else ''
            write_terminal_line(screen, height - 1, error or f'{len(marked)} selected{position}', curses.A_DIM)
        screen.refresh()

        key = screen.get_wch()
        error = ''
        if key in ('\n', '\r', curses.KEY_ENTER):
            return language
        if key in ('q', 'Q', '\x1b'):
            return None
        if key in ('a', 'A') and not remove:
            label = read_terminal_field(screen, 'Add IDE', 'IDE name')
            if label is None:
                continue
            path = read_terminal_field(screen, 'Add IDE', 'Full path to the executable')
            if path is not None:
                if add_custom_shortcut(choices, marked, label, path):
                    cursor = len(choices) - 1
                else:
                    error = 'Enter a name and an absolute path to an executable file.'
            continue
        if not ids:
            continue
        if key == ' ':
            marked.symmetric_difference_update({ids[cursor]})
        else:
            cursor = move_terminal_cursor(key, cursor, len(ids))


def pick_language_numbered(language):
    previews = language_previews()
    codes = {str(index): code for index, code in enumerate(previews, 1)}
    print('\n1/2  Choose Nautilus shortcut language')
    for index, code in codes.items():
        selected = '*' if code == language else ' '
        print(f'  {index}. {selected} {previews[code]}')
    while True:
        action = input('Number to select, Enter to keep the current language, q to cancel: ').strip().lower()
        if action == 'q':
            return None
        if not action:
            return language
        if action in codes:
            return codes[action]
        print('Invalid option.')


def pick_shortcuts_numbered(choices, marked, remove, language):
    if not remove:
        language = pick_language_numbered(language)
        if language is None:
            return None

    while True:
        print('\nSelect the shortcuts to remove.' if remove else '\n2/2  Choose Nautilus shortcuts')
        if not choices:
            print('No IDEs detected.')
        ids = list(choices)
        for index, ide_id in enumerate(ids, 1):
            check = 'x' if ide_id in marked else ' '
            print(f'  {index:2}. [{check}] {shortcut_label(ide_id, choices)}')

        if not remove:
            print(f'Menu language: {MENU_LANGUAGES[language][0]}')
        extra = '' if remove else ', a to add an IDE'
        action = input(f'Number to toggle{extra}, Enter to confirm, q to cancel: ').strip().lower()
        if action == 'q':
            return None
        if not action:
            return language
        if action == 'a' and not remove:
            label = input('IDE name: ')
            path = input('Full path to the executable: ')
            if not add_custom_shortcut(choices, marked, label, path):
                print('Enter a name and an absolute path to an executable file.')
            continue
        try:
            index = int(action)
        except ValueError:
            index = 0
        if 1 <= index <= len(ids):
            marked.symmetric_difference_update({ids[index - 1]})
        else:
            print('Invalid option.')


def pick_shortcuts(choices, marked, remove, language):
    terminal = os.environ.get('TERM')
    if curses and sys.stdin.isatty() and sys.stdout.isatty() and terminal not in (None, '', 'dumb'):
        try:
            return curses.wrapper(pick_shortcuts_terminal, choices, marked, remove, language)
        except curses.error:
            pass
    return pick_shortcuts_numbered(choices, marked, remove, language)


def manage_shortcuts(remove, destination=None):
    shortcuts, language = read_settings()
    choices = dict(shortcuts)
    if not remove:
        for ide_id, (label, _) in IDES.items():
            saved_path = shortcuts.get(ide_id, ('', ''))[1]
            launcher = find_launcher(ide_id, saved_path)
            if launcher:
                choices[ide_id] = (label, launcher)
            elif ide_id == 'phpstorm' and not saved_path:
                # The legacy default represents PhpStorm only when it is available.
                choices.pop(ide_id, None)

    marked = set() if remove else set(shortcuts).intersection(choices)
    if remove and not choices:
        print('No shortcuts configured.')
        return True

    language = pick_shortcuts(choices, marked, remove, language)
    if language is None:
        return False

    kept = set(choices).difference(marked) if remove else marked
    selection = {ide_id: entry for ide_id, entry in choices.items() if ide_id in kept}
    save_settings(selection, language, destination)
    if destination is None:
        print('Shortcuts removed.' if remove and marked else 'Shortcuts saved.')
    return True


def shortcut_cli(args):
    if len(args) == 1 and args[0] in ('--configure', '--remove'):
        destination = None
    elif len(args) == 2 and args[0] in ('--stage-selection', '--apply-selection'):
        destination = Path(args[1])
    else:
        sys.exit(f'Usage: {sys.argv[0]} --configure | --remove')

    try:
        if args[0] == '--apply-selection':
            save_settings(*read_settings(destination))
            return 0
        confirmed = manage_shortcuts(remove=args[0] == '--remove', destination=destination)
    except (EOFError, KeyboardInterrupt):
        confirmed = False
    except (OSError, ValueError) as error:
        sys.exit(f'Could not configure shortcuts. {error}')

    if confirmed:
        return 0
    if destination is not None:
        return 2
    print('Selection canceled.')
    return 0


def restart_nautilus():
    if not (os.environ.get('WAYLAND_DISPLAY') or os.environ.get('DISPLAY')):
        print('Restart postponed. No graphical session is available.')
        return 0

    from gi.repository import Gio, GLib

    def nautilus_owner():
        try:
            return bus.call_sync(
                'org.freedesktop.DBus', '/org/freedesktop/DBus', 'org.freedesktop.DBus',
                'GetNameOwner', GLib.Variant('(s)', ('org.gnome.Nautilus',)), None,
                Gio.DBusCallFlags.NO_AUTO_START, 2000, None,
            ).unpack()[0]
        except GLib.Error as error:
            if Gio.DBusError.get_remote_error(error) == 'org.freedesktop.DBus.Error.NameHasNoOwner':
                return None
            raise

    def wait_for_owner_change(previous):
        deadline = monotonic() + 8
        while monotonic() < deadline:
            owner = nautilus_owner()
            if owner != previous:
                return owner
            sleep(0.1)
        raise TimeoutError('Timed out waiting for Nautilus to change state.')

    try:
        bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
        owner = nautilus_owner()
    except GLib.Error:
        print('Restart postponed. Could not query the graphical session bus.')
        return 0

    if owner:
        try:
            windows = bus.call_sync(
                owner, '/org/freedesktop/FileManager1', 'org.freedesktop.DBus.Properties',
                'Get', GLib.Variant('(ss)', ('org.freedesktop.FileManager1', 'OpenWindowsWithLocations')),
                None, Gio.DBusCallFlags.NO_AUTO_START, 2000, None,
            ).unpack()[0]
            count = len(windows)
            window_label = 'window' if count == 1 else 'windows'
            warning = f'Nautilus has {count} open {window_label}.' if count else ''
        except GLib.Error:
            warning = 'Could not check whether Nautilus has open windows.'

        if warning:
            print(f'{warning} Restarting will close all open windows and tabs.')
            try:
                answer = input('Restart now? [y/N] ').strip().lower() if sys.stdin.isatty() else ''
            except (EOFError, KeyboardInterrupt):
                answer = ''
            if answer not in ('s', 'sim', 'y', 'yes'):
                print('Restart postponed.')
                return 0

    try:
        current_owner = owner
        if owner:
            if nautilus_owner() != owner:
                print('Restart postponed. Nautilus changed state during confirmation.')
                return 0
            run(['nautilus', '--quit'], check=True, timeout=10, stdin=DEVNULL)
            current_owner = wait_for_owner_change(owner)
        Popen(['nautilus'], stdin=DEVNULL, stdout=DEVNULL, stderr=DEVNULL, start_new_session=True)
        if current_owner is None:
            wait_for_owner_change(None)
    except (GLib.Error, OSError, SubprocessError) as error:
        print(f'Could not restart Nautilus. {error}', file=sys.stderr)
        return 1

    print('Nautilus restarted.' if owner else 'Nautilus opened.')
    return 0


if __name__ == '__main__':
    if sys.argv[1:] == ['--restart-nautilus']:
        sys.exit(restart_nautilus())

    try:
        import curses
    except ImportError:
        curses = None

    sys.exit(shortcut_cli(sys.argv[1:]))


# nautilus-python loads the API version matching the running file manager.
from gi.repository import Gio, GLib, GObject, Nautilus


class PhpStormExtension(GObject.GObject, Nautilus.MenuProvider):

    def launch_ide(self, menu, ide_id, label, launcher, paths):
        if not shutil.which(launcher):
            self.show_error_popup(f'{label} could not be found', 'The executable is no longer available.')
            return

        # OpenIDEA's graphical launcher accepts one positional path per invocation.
        selections = [[path] for path in paths] if ide_id == 'openidea' else [paths]
        for selection in selections:
            command = [launcher]
            if ide_id == 'phpstorm' and NEWWINDOW:
                command.append('--new-window')
            command.extend(selection)
            try:
                process = Gio.Subprocess.new(command, Gio.SubprocessFlags.NONE)
                process.wait_check_async(None, self.on_launch_finished, label)
            except GLib.Error as error:
                self.show_error_popup(f'Could not open {label}', error.message)
                break

    def on_launch_finished(self, process, result, label):
        try:
            process.wait_check_finish(result)
        except GLib.Error as error:
            self.show_error_popup(f'Could not open {label}', error.message)

    def get_file_items(self, *args):
        return self.get_open_items('files', args[-1])

    def get_background_items(self, *args):
        return self.get_open_items('folder', [args[-1]])

    def get_open_items(self, context, files):
        paths = [file.get_location().get_path() for file in files]
        if not paths or not all(paths):
            return []

        try:
            shortcuts, language = read_settings()
        except (OSError, ValueError) as error:
            print(f'Could not read the IDE shortcuts. {error}', file=sys.stderr)
            return []

        _, template = MENU_LANGUAGES[language]
        items = []
        for ide_id, (label, saved_path) in shortcuts.items():
            launcher = find_launcher(ide_id, saved_path)
            if launcher:
                item = Nautilus.MenuItem(
                    name=f'PhpStormExtension::{context}_{ide_id}',
                    label=template.format(ide=label),
                )
                item.connect('activate', self.launch_ide, ide_id, label, launcher, paths)
                items.append(item)
        return items

    def show_error_popup(self, title, message):
        try:
            Popen(['zenity', '--error', '--title', title, '--text', message])
        except OSError as error:
            print(f'{title}: {message}\nCould not start Zenity: {error}')
