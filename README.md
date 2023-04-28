# phpstorm-nautilus

> Este script cria um atalho no menu de clique direito do Ubuntu para abrir o diretório no PHPStorm.

## Pré-requisitos

* Ubuntu 20.04 ou superior (não testado em versões anteriores)
* PHPStorm

## Instalando

Para configurar o atalho, rode o seguinte comando:

Ubuntu:
```
wget -qO- https://raw.githubusercontent.com/terciotales/phpstorm-nautilus/main/install.sh | bash
```


## Desinstalando

Para desinstalar o atalho, rode o seguinte comando:

Ubuntu:
```
rm -f ~/.local/share/nautilus-python/extensions/code-nautilus.py
```
