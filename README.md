# hx32 download manager
# Last updated: 2026-06-28 — v3.0.0

hx32 download manager is a linux-only gtk4 app written in python.

it lets you add a download url, track progress, cancel downloads, and save files to your downloads folder.

the ui includes tabs for downloads, themes, and settings so users can customize the app.

## install

1. install gtk4 and python binding packages:

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0
```

2. run the app from the project folder:

```bash
cd path/to/project
python3 hx32_download_manager.py
```

3. or install the Debian package once built or downloaded:

```bash
sudo dpkg -i hx32-download-manager_3.0.0_amd64.deb
```

4. if an older version is installed, run the uninstaller before updating:

```bash
sudo ./uninstall_hx32_download_manager.sh
```

## release

- version: 3.0.0
- packages: `hx32-download-manager_3.0.0_amd64.deb` (Linux) and `hx32-download-manager.exe` (Windows)
- notes: UI improvements, tabs, improved theme, and release artifacts for Linux and Windows
- install the Debian package from the project root or download the Windows executable from the GitHub release

## usage

- enter a file url in the input field
- click `+ new download`
- select a download task to view details
- use the themes tab to change the app style
- use the settings tab to change the save folder

## features

- real file download from url using python
- dark purple ui with theme support
- tabs for downloads, themes, and settings
- change download destination folder
- cancel active downloads
- save completed files to your downloads folder

## note

- linux only
- works with `python3`
- files are saved under `~/Downloads` by default
- this repository includes the 2.0.0 alpha Debian package
