#!/usr/bin/env python3
# Last updated: 2026-06-30 — v5.0.0

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio, GLib, Gdk
from pathlib import Path
import os
import re
import threading
import urllib.parse
import urllib.request
import urllib.error

class DownloadTask:
    def __init__(self, task_id, url, file_name, save_path, row, progress_bar, status_label, action_button):
        self.id = task_id
        self.url = url
        self.file_name = file_name
        self.save_path = save_path
        self.progress = 0.0
        self.canceled = False
        self.completed = False
        self.row = row
        self.progress_bar = progress_bar
        self.status_label = status_label
        self.action_button = action_button

class HX32DownloadManager(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='com.hx32.downloadmanager')
        self.tasks = []
        self.next_id = 1
        self.download_dir = os.path.expanduser('~/Downloads')
        self.theme_name = 'theme-violet'
        self.connect('activate', self.on_activate)

    def on_activate(self, app):
        print('HX32 activate')
        self.window = Gtk.ApplicationWindow(application=app)
        self.window.set_title('HX32 Download Manager')
        self.window.set_default_size(1120, 760)
        self.window.set_margin_start(16)
        self.window.set_margin_end(16)
        self.window.set_margin_top(16)
        self.window.set_margin_bottom(16)
        self.window.add_css_class(self.theme_name)

        style_provider = Gtk.CssProvider()
        style_provider.load_from_path(self.find_style_path())
        Gtk.StyleContext.add_provider_for_display(Gdk.Display.get_default(), style_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        header = Gtk.HeaderBar.new()
        header.set_show_title_buttons(True)

        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        title_box.set_halign(Gtk.Align.START)

        title_widget = Gtk.Label(label='HX32 Download Manager')
        title_widget.add_css_class('title-label')
        title_widget.set_xalign(0)

        subtitle_widget = Gtk.Label(label='a modern download manager')
        subtitle_widget.add_css_class('subtitle-label')
        subtitle_widget.set_xalign(0)

        title_box.append(title_widget)
        title_box.append(subtitle_widget)
        header.set_title_widget(title_box)
        self.window.set_titlebar(header)

        page_downloads = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)

        title_label = Gtk.Label(label='HX32: download better')
        title_label.add_css_class('title-label')
        title_label.set_xalign(0)
        title_label.set_wrap(True)

        subtitle_label = Gtk.Label(label='add a url, start downloading and track progress live.')
        subtitle_label.add_css_class('subtitle-label')
        subtitle_label.set_xalign(0)
        subtitle_label.set_wrap(True)

        action_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        action_row.set_halign(Gtk.Align.FILL)

        self.url_entry = Gtk.Entry()
        self.url_entry.set_placeholder_text('enter the download url')
        self.url_entry.add_css_class('entry-field')
        self.url_entry.set_hexpand(True)
        self.url_entry.connect('activate', self.on_add_download)

        add_button = Gtk.Button(label='+ new download')
        add_button.add_css_class('primary-button')
        add_button.connect('clicked', self.on_add_download)

        assist_button = Gtk.Button(label='Find link')
        assist_button.add_css_class('secondary-button')
        assist_button.connect('clicked', self.on_assist_link)

        action_row.append(self.url_entry)
        action_row.append(assist_button)
        action_row.append(add_button)

        top_panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        top_panel.add_css_class('top-toolbar')
        top_panel.set_hexpand(True)
        top_panel.set_margin_bottom(10)
        top_panel.append(title_label)
        top_panel.append(subtitle_label)
        top_panel.append(action_row)

        page_downloads.append(top_panel)

        self.assistant_status = Gtk.Label(label='Link assistant ready.')
        self.assistant_status.add_css_class('details-text')
        self.assistant_status.set_xalign(0)
        top_panel.append(self.assistant_status)

        # Single listbox with inline filter buttons (All / Active / Completed)
        self.list_box = Gtk.ListBox()
        self.list_box.set_selection_mode(Gtk.SelectionMode.SINGLE)
        self.list_box.add_css_class('download-list')
        self.list_box.set_vexpand(True)
        self.list_box.connect('row-selected', self.on_row_selected)

        # Filter toolbar
        filter_bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        filter_bar.set_halign(Gtk.Align.START)
        self.filter_all = Gtk.ToggleButton.new_with_label('All')
        self.filter_active = Gtk.ToggleButton.new_with_label('Active')
        self.filter_completed = Gtk.ToggleButton.new_with_label('Completed')
        self.filter_all.set_active(True)
        for btn in (self.filter_all, self.filter_active, self.filter_completed):
            btn.add_css_class('tab-button')
            btn.connect('toggled', self.on_filter_toggled)
            filter_bar.append(btn)

        page_downloads.append(filter_bar)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.list_box)
        scrolled.set_vexpand(True)
        scrolled.set_min_content_width(540)

        self.details_panel, self.details_widgets = self.build_details_panel()

        dashboard = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=18)
        dashboard.set_hexpand(True)
        dashboard.append(scrolled)
        dashboard.append(self.details_panel)

        page_downloads.append(dashboard)

        page_prelink = self.build_prelink_page()
        page_theme = self.build_theme_page()
        page_settings = self.build_settings_page()

        notebook = Gtk.Notebook()
        notebook.add_css_class('main-tabs')
        notebook.append_page(page_downloads, Gtk.Label(label='Downloads'))
        notebook.append_page(page_prelink, Gtk.Label(label='Pre-download'))
        notebook.append_page(page_theme, Gtk.Label(label='Themes'))
        notebook.append_page(page_settings, Gtk.Label(label='Settings'))

        self.window.set_child(notebook)
        self.window.present()

    def build_details_panel(self):
        details = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        details.add_css_class('details-card')
        details.set_hexpand(True)
        details.set_vexpand(True)

        details_title = Gtk.Label(label='download details')
        details_title.add_css_class('details-title')
        details_title.set_xalign(0)

        description = Gtk.Label(label='select a task to view the path, status, and progress.')
        description.add_css_class('details-text')
        description.set_wrap(True)
        description.set_xalign(0)

        self.details_status = Gtk.Label(label='status: —')
        self.details_status.add_css_class('details-text')
        self.details_status.set_xalign(0)

        self.details_url = Gtk.Label(label='URL: —')
        self.details_url.add_css_class('details-text')
        self.details_url.set_wrap(True)
        self.details_url.set_xalign(0)

        self.details_progress = Gtk.ProgressBar()
        self.details_progress.add_css_class('details-progress')
        self.details_progress.set_hexpand(True)

        self.details_dir = Gtk.Label(label=f'Path: {self.download_dir}')
        self.details_dir.add_css_class('details-text')
        self.details_dir.set_wrap(True)
        self.details_dir.set_xalign(0)

        details.append(details_title)
        details.append(description)
        details.append(self.details_status)
        details.append(self.details_url)
        details.append(self.details_dir)
        details.append(self.details_progress)

        widgets = {
            'status': self.details_status,
            'url': self.details_url,
            'progress': self.details_progress,
        }
        return details, widgets

    def on_add_download(self, widget):
        url = self.url_entry.get_text().strip()
        if not url:
            return

        task_id = self.next_id
        self.next_id += 1
        file_name = self.extract_file_name(url, task_id)

        progress_bar = Gtk.ProgressBar()
        progress_bar.add_css_class('download-progress')

        status_label = Gtk.Label(label='Preparing...')
        status_label.add_css_class('status-label')
        status_label.set_xalign(0)

        action_button = Gtk.Button(label='Annuler')
        action_button.add_css_class('secondary-button')

        task_row = self.create_download_row(file_name, progress_bar, status_label, action_button)
        task_row.download_id = task_id

        os.makedirs(self.download_dir, exist_ok=True)
        save_path = os.path.join(self.download_dir, file_name)

        task = DownloadTask(task_id, url, file_name, save_path, task_row, progress_bar, status_label, action_button)
        self.tasks.append(task)
        self.list_box.append(task_row)
        self.url_entry.set_text('')

        action_button.connect('clicked', self.on_cancel_download, task_id)
        self.start_download(task)

    def on_assist_link(self, button):
        url = self.url_entry.get_text().strip()
        if not url:
            self.assistant_status.set_text('Enter a URL to search for a download link.')
            return

        button.set_sensitive(False)
        self.assistant_status.set_text('Looking for a good download link...')
        thread = threading.Thread(target=self.find_direct_link, args=(url, button), daemon=True)
        thread.start()

    def on_find_prelink(self, button):
        url = self.prelink_entry.get_text().strip()
        if not url:
            self.prelink_result.set_text('Enter a URL to inspect.')
            return

        button.set_sensitive(False)
        self.prelink_result.set_text('Analyzing link...')
        thread = threading.Thread(target=self.resolve_prelink, args=(url, button), daemon=True)
        thread.start()

    def resolve_prelink(self, url, button):
        candidate = self.resolve_download_link(url)
        if candidate:
            GLib.idle_add(self.prelink_result.set_text, f'Direct link found: {candidate}')
            GLib.idle_add(self.copy_button.set_sensitive, True)
            GLib.idle_add(self.prelink_icon.set_from_icon_name, self.get_icon_for_link(candidate), Gtk.IconSize.BUTTON)
            GLib.idle_add(self.copy_button.set_tooltip_text, candidate)
            self.prelink_value = candidate
        else:
            GLib.idle_add(self.prelink_result.set_text, 'No direct download link was found.')
            GLib.idle_add(self.copy_button.set_sensitive, False)
            self.prelink_value = None
        GLib.idle_add(button.set_sensitive, True)

    def on_copy_prelink(self, button):
        if getattr(self, 'prelink_value', None):
            display = Gdk.Display.get_default()
            if display:
                clipboard = display.get_clipboard()
                text_value = GLib.Variant.new_string(self.prelink_value)
                content = Gdk.ContentProvider.new_for_value(text_value)
                clipboard.set_content(content)
                self.prelink_result.set_text('Pre-link copied. Paste it into the download field.')
                self.url_entry.set_text(self.prelink_value)
            else:
                self.prelink_result.set_text('Clipboard is unavailable.')

    def get_icon_for_link(self, url):
        link = url.split('?')[0].lower()
        icons = {
            '.exe': 'application-x-executable-symbolic',
            '.zip': 'package-x-generic-symbolic',
            '.tar.gz': 'package-x-generic-symbolic',
            '.gz': 'package-x-generic-symbolic',
            '.deb': 'package-x-generic-symbolic',
            '.pdf': 'x-office-document-symbolic',
            '.mp4': 'video-x-generic-symbolic',
            '.mp3': 'audio-x-generic-symbolic',
            '.jpg': 'image-jpeg-symbolic',
            '.jpeg': 'image-jpeg-symbolic',
            '.png': 'image-png-symbolic',
            '.svg': 'image-svg+xml-symbolic',
            '.txt': 'text-x-generic-symbolic',
            '.docx': 'x-office-document-symbolic',
            '.xlsx': 'x-office-spreadsheet-symbolic',
        }
        for ext, icon in icons.items():
            if link.endswith(ext):
                return icon
        return 'text-x-generic-symbolic'

    def find_direct_link(self, url, button):
        candidate = self.resolve_download_link(url)
        if candidate:
            GLib.idle_add(self.url_entry.set_text, candidate)
            GLib.idle_add(self.assistant_status.set_text, 'Direct download link suggested.')
        else:
            GLib.idle_add(self.assistant_status.set_text, 'No direct download link was found.')
        GLib.idle_add(button.set_sensitive, True)

    def resolve_download_link(self, url):
        if self.is_probably_direct_file(url):
            return url
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'HX32 Download Manager/4.0'})
            with urllib.request.urlopen(request, timeout=20) as response:
                if response.getheader('Content-Disposition'):
                    return url
                content_type = response.getheader('Content-Type', '').lower()
                if 'text/html' in content_type:
                    html = response.read(65536).decode('utf-8', errors='ignore')
                    direct_link = self.extract_link_from_html(html, url)
                    if direct_link:
                        return direct_link
                if 'application' in content_type or 'octet-stream' in content_type:
                    return url
        except Exception:
            pass
        return None

    def extract_link_from_html(self, html, base_url):
        links = re.findall(r'href=[\"\']([^\"\']+)[\"\']', html, re.I)
        for link in links:
            if link.startswith('//'):
                link = 'https:' + link
            if self.is_probably_direct_file(link):
                if link.startswith('http'):
                    return link
                if link.startswith('/'):
                    return urllib.parse.urljoin(base_url, link)
        return None

    def is_probably_direct_file(self, url):
        target = url.split('?')[0].lower()
        extensions = ('.exe', '.zip', '.tar.gz', '.gz', '.deb', '.msi', '.iso', '.pdf', '.mp4', '.mp3', '.jpg', '.jpeg', '.png', '.svg', '.txt', '.docx', '.xlsx')
        return any(target.endswith(ext) for ext in extensions)

    def on_cancel_download(self, button, task_id):
        for task in self.tasks:
            if task.id == task_id and not task.completed:
                task.canceled = True
                task.status_label.set_text('Canceled')
                task.action_button.set_label('Canceled')
                task.action_button.set_sensitive(False)
                break

    def update_download(self, task_id, progress, status):
        for task in self.tasks:
            if task.id == task_id:
                if task.canceled:
                    task.status_label.set_text('Annulé')
                    return False
                task.progress = progress
                task.progress_bar.set_fraction(progress)
                task.status_label.set_text(status)
                if progress >= 1.0:
                    task.completed = True
                    task.action_button.set_label('Terminé')
                    task.action_button.set_sensitive(False)
                    task.completed = True
                    self.refresh_list_visibility()
                    return False
                return False
        return False

    def start_download(self, task):
        thread = threading.Thread(target=self.download_file, args=(task,), daemon=True)
        thread.start()

    def download_file(self, task):
        request = urllib.request.Request(task.url, headers={'User-Agent': 'HX32 Download Manager/1.0'})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                total = response.getheader('Content-Length')
                total_bytes = int(total) if total and total.isdigit() else None
                written = 0
                temp_path = task.save_path + '.part'
                with open(temp_path, 'wb') as out_file:
                    while not task.canceled:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        out_file.write(chunk)
                        written += len(chunk)
                        if total_bytes:
                            fraction = min(1.0, written / total_bytes)
                            status_text = f'Downloading — {int(fraction * 100)}%'
                        else:
                            fraction = 0.0
                            status_text = f'Downloading — {written // 1024} KiB'
                        GLib.idle_add(self.update_download, task.id, fraction, status_text)
                if task.canceled:
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
                    return
                os.replace(temp_path, task.save_path)
                GLib.idle_add(self.update_download, task.id, 1.0, 'Download complete')
        except urllib.error.HTTPError as err:
            GLib.idle_add(self.update_download, task.id, task.progress, f'HTTP error {err.code}')
        except urllib.error.URLError as err:
            GLib.idle_add(self.update_download, task.id, task.progress, 'invalid url or network error')
        except Exception:
            GLib.idle_add(self.update_download, task.id, task.progress, 'download error')

    def on_row_selected(self, listbox, row):
        if row is None:
            return
        task_id = getattr(row, 'download_id', None)
        for task in self.tasks:
            if task.id == task_id:
                status_label = 'Canceled' if task.canceled else 'Complete' if task.completed else 'Downloading'
                self.details_status.set_text(f'Status: {status_label}')
                self.details_url.set_text(f'URL: {task.url}')
                self.details_dir.set_text(f'Path: {task.save_path}')
                self.details_progress.set_fraction(task.progress)
                break

    def create_download_row(self, file_name, progress_bar, status_label, action_button):
        row = Gtk.ListBoxRow()
        row.add_css_class('download-row')

        row_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        row_box.set_margin_start(14)
        row_box.set_margin_end(14)
        row_box.set_margin_top(14)
        row_box.set_margin_bottom(14)

        header = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        header.set_halign(Gtk.Align.FILL)

        file_label = Gtk.Label(label=file_name)
        file_label.add_css_class('download-name')
        file_label.set_xalign(0)
        file_label.set_hexpand(True)

        header.append(file_label)
        header.append(action_button)

        row_box.append(header)
        row_box.append(progress_bar)
        row_box.append(status_label)
        row.set_child(row_box)
        return row

    def save_task_file(self, task):
        try:
            content = f"File {task.file_name} downloaded from {task.url}\n"
            Path(task.save_path).write_text(content, encoding='utf-8')
        except Exception:
            pass

    def extract_file_name(self, url, task_id):
        cleaned = url.split('?')[0]
        candidate = [segment for segment in cleaned.split('/') if segment][-1] if '/' in cleaned else cleaned
        if not candidate or '.' not in candidate:
            return f'fichier-{task_id}.bin'
        return candidate

    def on_filter_toggled(self, button):
        # Ensure only one filter is active at a time
        if button is self.filter_all and button.get_active():
            self.filter_active.set_active(False)
            self.filter_completed.set_active(False)
        elif button is self.filter_active and button.get_active():
            self.filter_all.set_active(False)
            self.filter_completed.set_active(False)
        elif button is self.filter_completed and button.get_active():
            self.filter_all.set_active(False)
            self.filter_active.set_active(False)
        # refresh visibility
        self.refresh_list_visibility()

    def refresh_list_visibility(self):
        show_all = self.filter_all.get_active()
        show_active = self.filter_active.get_active()
        show_completed = self.filter_completed.get_active()
        for task in self.tasks:
            try:
                if show_all:
                    task.row.set_visible(True)
                elif show_active:
                    task.row.set_visible(not task.completed and not task.canceled)
                elif show_completed:
                    task.row.set_visible(task.completed)
            except Exception:
                pass

    def build_prelink_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_margin_top(12)
        page.set_margin_end(18)
        page.set_margin_start(18)
        page.set_margin_bottom(18)

        title = Gtk.Label(label='pre-download links')
        title.add_css_class('details-title')
        title.set_xalign(0)

        subtitle = Gtk.Label(label='Inspect page URLs, copy the direct download link, then paste it into the downloader.')
        subtitle.add_css_class('details-text')
        subtitle.set_wrap(True)
        subtitle.set_xalign(0)

        self.prelink_entry = Gtk.Entry()
        self.prelink_entry.set_placeholder_text('enter a page or file URL for preview')
        self.prelink_entry.add_css_class('entry-field')
        self.prelink_entry.set_hexpand(True)

        find_button = Gtk.Button(label='Find pre-link')
        find_button.add_css_class('primary-button')
        find_button.connect('clicked', self.on_find_prelink)

        self.prelink_result = Gtk.Label(label='No link selected yet.')
        self.prelink_result.add_css_class('details-text')
        self.prelink_result.set_wrap(True)
        self.prelink_result.set_xalign(0)

        self.copy_button = Gtk.Button(label='Copy pre-link')
        self.copy_button.add_css_class('secondary-button')
        self.copy_button.set_sensitive(False)
        self.copy_button.connect('clicked', self.on_copy_prelink)

        self.prelink_icon = Gtk.Image.new_from_icon_name('text-x-generic-symbolic', Gtk.IconSize.BUTTON)
        self.prelink_icon.set_pixel_size(48)

        button_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        button_row.append(find_button)
        button_row.append(self.copy_button)

        page.append(title)
        page.append(subtitle)
        page.append(self.prelink_entry)
        page.append(button_row)
        page.append(self.prelink_icon)
        page.append(self.prelink_result)
        return page

    def build_theme_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_margin_top(12)
        page.set_margin_end(18)
        page.set_margin_start(18)
        page.set_margin_bottom(18)

        title = Gtk.Label(label='select a theme')
        title.add_css_class('details-title')
        title.set_xalign(0)

        subtitle = Gtk.Label(label='customize your manager with a dark theme.')
        subtitle.add_css_class('details-text')
        subtitle.set_wrap(True)
        subtitle.set_xalign(0)

        theme_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        theme_box.set_halign(Gtk.Align.START)

        self.theme_combo = Gtk.ComboBoxText()
        self.theme_combo.append_text('Violet')
        self.theme_combo.append_text('Graphite')
        self.theme_combo.append_text('Neon')
        self.theme_combo.set_active(0)
        self.theme_combo.connect('changed', self.on_theme_changed)
        self.theme_combo.add_css_class('entry-field')

        theme_box.append(self.theme_combo)

        page.append(title)
        page.append(subtitle)
        page.append(theme_box)
        return page

    def build_settings_page(self):
        page = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=18)
        page.set_margin_top(12)
        page.set_margin_end(18)
        page.set_margin_start(18)
        page.set_margin_bottom(18)

        title = Gtk.Label(label='download settings')
        title.add_css_class('details-title')
        title.set_xalign(0)

        subtitle = Gtk.Label(label='choose the destination folder and enable options.')
        subtitle.add_css_class('details-text')
        subtitle.set_wrap(True)
        subtitle.set_xalign(0)

        self.dir_entry = Gtk.Entry()
        self.dir_entry.set_text(self.download_dir)
        self.dir_entry.add_css_class('entry-field')
        self.dir_entry.set_hexpand(True)

        save_dir_button = Gtk.Button(label='save folder')
        save_dir_button.add_css_class('primary-button')
        save_dir_button.connect('clicked', self.on_save_directory)

        option_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        option_box.set_valign(Gtk.Align.CENTER)

        self.notify_switch = Gtk.Switch()
        self.notify_switch.set_active(True)
        self.notify_switch.add_css_class('secondary-button')
        notify_label = Gtk.Label(label='notifications enabled')
        notify_label.add_css_class('details-text')
        notify_label.set_xalign(0)

        option_box.append(self.notify_switch)
        option_box.append(notify_label)

        page.append(title)
        page.append(subtitle)
        page.append(self.dir_entry)
        page.append(save_dir_button)
        page.append(option_box)
        return page

    def on_theme_changed(self, combo):
        selected = combo.get_active_text()
        if selected == 'Graphite':
            theme = 'theme-graphite'
        elif selected == 'Neon':
            theme = 'theme-neon'
        else:
            theme = 'theme-violet'
        self.window.remove_css_class(self.theme_name)
        self.theme_name = theme
        self.window.add_css_class(theme)

    def on_save_directory(self, button):
        path = self.dir_entry.get_text().strip()
        if path:
            expanded = os.path.expanduser(path)
            os.makedirs(expanded, exist_ok=True)
            self.download_dir = expanded
            self.details_dir.set_text(f'Path: {self.download_dir}')

    def find_style_path(self):
        local_path = os.path.join(os.path.dirname(__file__), 'assets', 'style.css')
        if os.path.exists(local_path):
            return local_path
        packaged_path = os.path.join(os.path.dirname(__file__), '..', 'share', 'hx32-download-manager', 'style.css')
        if os.path.exists(packaged_path):
            return packaged_path
        raise FileNotFoundError('style.css not found')


def main():
    app = HX32DownloadManager()
    app.run(None)

if __name__ == '__main__':
    main()
