# hx32 download manager

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
cd ~/Téléchargements/Project
python3 hx32_download_manager.py
```

## usage

- enter a file url in the input field
- click `+ nouveau téléchargement`
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
- files are saved under `~/Téléchargements` by default
