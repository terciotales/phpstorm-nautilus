# PhpStorm Nautilus extension. Released to the public domain.

import os
import shutil
from subprocess import Popen

# nautilus-python loads the API version matching the running file manager.
from gi.repository import Gio, GLib, GObject, Nautilus


NEWWINDOW = False


def find_phpstorm():
    override = os.environ.get('PHPSTORM_LAUNCHER')
    if override:
        return shutil.which(os.path.expanduser(override))

    toolbox = os.path.expanduser('~/.local/share/JetBrains/Toolbox')
    candidates = (
        'phpstorm',
        os.path.expanduser('~/.local/bin/phpstorm'),
        os.path.join(toolbox, 'scripts', 'phpstorm'),
        os.path.join(toolbox, 'apps', 'phpstorm', 'bin', 'phpstorm.sh'),
        '/snap/bin/phpstorm',
    )
    for candidate in candidates:
        launcher = shutil.which(candidate)
        if launcher:
            return launcher
    return None


class PhpStormExtension(GObject.GObject, Nautilus.MenuProvider):

    def launch_phpstorm(self, menu, paths):
        launcher = find_phpstorm()
        if launcher is None:
            self.show_error_popup(
                'PhpStorm could not be found',
                'Add the executable to PATH or set PHPSTORM_LAUNCHER in the graphical session.',
            )
            return

        command = [launcher]
        if NEWWINDOW:
            command.append('--new-window')
        command.extend(paths)

        try:
            process = Gio.Subprocess.new(command, Gio.SubprocessFlags.NONE)
            process.wait_check_async(None, self.on_launch_finished)
        except GLib.Error as error:
            self.show_error_popup('Could not open PhpStorm', error.message)

    def on_launch_finished(self, process, result):
        try:
            process.wait_check_finish(result)
        except GLib.Error as error:
            self.show_error_popup('Could not open PhpStorm', error.message)

    def get_file_items(self, *args):
        return self.get_open_items('PhpStormOpen', args[-1])

    def get_background_items(self, *args):
        return self.get_open_items('PhpStormOpenBackground', [args[-1]])

    def get_open_items(self, name, files):
        paths = [file.get_location().get_path() for file in files]
        if not paths or not all(paths):
            return []

        item = Nautilus.MenuItem(name=name, label='Open in PhpStorm')
        item.connect('activate', self.launch_phpstorm, paths)
        return [item]

    def show_error_popup(self, title, message):
        try:
            Popen(['zenity', '--error', '--title', title, '--text', message])
        except OSError as error:
            print(f'{title}: {message}\nCould not start Zenity: {error}')
