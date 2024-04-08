#! /bin/sh

# linux
pyinstaller dictionary.spec
pipreqs .
wine $EXE_DIR/pip.exe install -r requirements.txt
wine $EXE_DIR/pyinstaller.exe dictionary.spec
