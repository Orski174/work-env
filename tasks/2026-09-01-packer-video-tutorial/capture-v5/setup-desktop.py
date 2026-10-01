#!/usr/bin/env python3
"""One-time clean XFCE framing in the dedicated capture VM (not a user's DE)."""
from pathlib import Path

home = Path('/admin')
config = home / '.config/xfce4'
config.mkdir(parents=True, exist_ok=True)
terminal = config / 'terminal'
terminal.mkdir(exist_ok=True)
(terminal / 'terminalrc').write_text('''[Configuration]
FontName=DejaVu Sans Mono 13
MiscDefaultGeometry=102x36
MiscMenubarDefault=FALSE
MiscToolbarDefault=FALSE
MiscBordersDefault=TRUE
MiscAlwaysShowTabs=FALSE
MiscConfirmClose=FALSE
MiscShowUnsafePasteDialog=FALSE
ColorUseTheme=FALSE
ColorBackground=#101318
ColorForeground=#e6edf3
BackgroundMode=TERMINAL_BACKGROUND_SOLID
ScrollingBar=TERMINAL_SCROLLBAR_NONE
TitleMode=TERMINAL_TITLE_REPLACE
TitleInitial=Packer to boxman
''')
panel = config / 'panel'
for index, name, icon, command in [
    (2, 'Terminal', 'utilities-terminal', 'xfce4-terminal --disable-server --geometry=102x36+20+65 --title="Packer to boxman" --command="bash --rcfile /var/lib/scds-recording/v5/pipeline/demo-bashrc"'),
    (3, 'Values sheet', 'accessories-text-editor', 'mousepad /admin/packer-tutorial/packer-values.txt'),
]:
    directory = panel / f'launcher-{index}'
    directory.mkdir(parents=True, exist_ok=True)
    (directory / 'demo.desktop').write_text(f'[Desktop Entry]\nType=Application\nName={name}\nIcon={icon}\nExec={command}\nPath=/admin/packer-tutorial\nTerminal=false\n')
conf = config / 'xfconf/xfce-perchannel-xml'
conf.mkdir(parents=True, exist_ok=True)
(conf / 'xfce4-panel.xml').write_text('''<?xml version="1.0" encoding="UTF-8"?>
<channel name="xfce4-panel" version="1.0">
 <property name="configver" type="int" value="2"/>
 <property name="panels" type="array"><value type="int" value="1"/>
  <property name="panel-1" type="empty">
   <property name="position" type="string" value="p=6;x=0;y=0"/>
   <property name="position-locked" type="bool" value="true"/>
   <property name="size" type="uint" value="36"/>
   <property name="length" type="uint" value="100"/>
   <property name="plugin-ids" type="array"><value type="int" value="1"/><value type="int" value="2"/><value type="int" value="3"/><value type="int" value="4"/></property>
  </property>
 </property>
 <property name="plugins" type="empty">
  <property name="plugin-1" type="string" value="applicationsmenu"><property name="show-button-title" type="bool" value="false"/></property>
  <property name="plugin-2" type="string" value="launcher"><property name="items" type="array"><value type="string" value="demo.desktop"/></property></property>
  <property name="plugin-3" type="string" value="launcher"><property name="items" type="array"><value type="string" value="demo.desktop"/></property></property>
  <property name="plugin-4" type="string" value="tasklist"/>
 </property>
</channel>
''')
