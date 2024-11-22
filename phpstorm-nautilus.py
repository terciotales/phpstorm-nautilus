# PhpStorm Nautilus Extension
#
# Place me in ~/.local/share/nautilus-python/extensions/,
# ensure you have python-nautilus package, restart Nautilus, and enjoy :)
#
# This script is released to the public domain.

import gi
gi.require_version('Nautilus', '4.0')
from gi.repository import Nautilus, GObject
from subprocess import call, Popen, PIPE
import os
import shutil

# always create new window?
NEWWINDOW = False

# what name do you want to see in the context menu?
PHPSTORMNAME = 'PhpStorm'

# path to phpstorm
PHPSTORM = None

# Caminho da pasta do usuário
user_home = os.path.expanduser("~")
# Caminho completo do executável do PhpStorm
phpstorm_cmd_path = shutil.which('phpstorm')

# Verifica se o PhpStorm está instalado
if phpstorm_cmd_path is not None:
    # Usa o comando do PhpStorm instalado globalmente se existir
    PHPSTORM = phpstorm_cmd_path
elif os.path.exists(f'{user_home}/.local/share/JetBrains/Toolbox/scripts/phpstorm'):
    # Usa o comando do PhpStorm instalado pelo JetBrains Toolbox
    PHPSTORM = f'{user_home}/.local/share/JetBrains/Toolbox/scripts/phpstorm'
elif os.path.exists(f'{user_home}/.local/share/JetBrains/Toolbox/apps/phpstorm/bin/phpstorm.sh'):
    # Usa o comando do PhpStorm instalado pelo JetBrains Toolbox na pasta apps
    PHPSTORM = f'{user_home}/.local/share/JetBrains/Toolbox/apps/phpstorm/bin/phpstorm.sh'

class PhpStormExtension(GObject.GObject, Nautilus.MenuProvider):

    def launch_phpstorm(self, menu, files):
        cmd_args = [PHPSTORM]

        if NEWWINDOW:
            cmd_args.append('--new-window')

        for file in files:
            filepath = file.get_location().get_path()
            cmd_args.append(filepath)

        if PHPSTORM is not None:
            try:
                Popen(cmd_args, stdout=PIPE, stderr=PIPE)
            except Exception as e:
               self.show_error_popup(f"Erro ao abrir {PHPSTORMNAME}", f"Falha ao executar o comando {PHPSTORM}\n\n{e}")
        else:
            self.show_error_popup(f"{PHPSTORMNAME} não encontrado", f"Verifique se o {PHPSTORMNAME} está instalado e tente novamente.")

    def get_file_items(self, *args):
        files = args[-1]
        item = Nautilus.MenuItem(
            name='PhpStormOpen',
            label='Abrir no ' + PHPSTORMNAME,
            tip='Opens the selected files with PhpStorm'
        )
        item.connect('activate', self.launch_phpstorm, files)

        return [item]

    def get_background_items(self, *args):
        file_ = args[-1]
        item = Nautilus.MenuItem(
            name='PhpStormOpenBackground',
            label='Abrir no ' + PHPSTORMNAME,
            tip='Opens the current directory in PhpStorm'
        )
        item.connect('activate', self.launch_phpstorm, [file_])

        return [item]

    def show_error_popup(self, title, message):
        try:
            # Use Popen to run zenity asynchronously
            Popen([
                'zenity',
                '--error',
                #'--width', '250',
                #'--height', '50',
                '--title', title,
                '--text', message
            ], stdout=PIPE, stderr=PIPE)
        except Exception as e:
            print(f"Error launching zenity: {e}")
