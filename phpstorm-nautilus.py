# PHPStorm Nautilus Extension
#
# Place me in ~/.local/share/nautilus-python/extensions/,
# ensure you have python-nautilus package, restart Nautilus, and enjoy :)
#
# This script is released to the public domain.

from gi.repository import Nautilus, GObject
from subprocess import call
import os

# path to phpstorm
PHPSTORM = 'phpstorm'

# what name do you want to see in the context menu?
PHPSTORMNAME = 'PHPStorm'

# always create new window?
NEWWINDOW = False

class PHPStormExtension(GObject.GObject, Nautilus.MenuProvider):

    def launch_phpstorm(self, menu, files):
        safepaths = ''
        args = ''

        for file in files:
            filepath = file.get_location().get_path()
            safepaths += '"' + filepath + '" '

        if NEWWINDOW:
            args = '--new-window '

        call(PHPSTORM + ' ' + args + safepaths + '&', shell=True)

    def get_file_items(self, *args):
        files = args[-1]
        item = Nautilus.MenuItem(
            name='PHPStormOpen',
            label='Abrir no ' + PHPSTORMNAME,
            tip='Opens the selected files with PHPStorm'
        )
        item.connect('activate', self.launch_phpstorm, files)

        return [item]

    def get_background_items(self, *args):
        file_ = args[-1]
        item = Nautilus.MenuItem(
            name='PHPStormOpenBackground',
            label='Abrir no ' + PHPSTORMNAME,
            tip='Opens the current directory in PHPStorm'
        )
        item.connect('activate', self.launch_phpstorm, [file_])

        return [item]
