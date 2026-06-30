// Last updated: 2026-06-30 — v4.0.0
use gtk4::prelude::*;
use gtk4::{Application, ApplicationWindow, Box as GtkBox, Button, Entry, HeaderBar, Label, ListBox, ListBoxRow, Orientation, ProgressBar, ScrolledWindow, SelectionMode, StyleContext};
use gtk4::gdk;
use glib::Continue;
use std::cell::{Cell, RefCell};
use std::rc::Rc;

#[derive(Clone)]
struct DownloadTask {
    id: u32,
    url: String,
    file_name: String,
    progress: f64,
    canceled: bool,
    progress_bar: ProgressBar,
    status_label: Label,
    action_button: Button,
}

struct AppState {
    tasks: RefCell<Vec<DownloadTask>>,
    next_id: Cell<u32>,
}

#[derive(Clone)]
struct DetailsWidgets {
    status: Label,
    url: Label,
    progress: ProgressBar,
}

fn main() {
    let app = Application::new(Some("com.hx32.downloadmanager"), Default::default());
    app.connect_activate(build_ui);
    app.run();
}

fn build_ui(app: &Application) {
    let display = gdk::Display::default();
    if let Some(display) = display {
        let provider = gtk4::CssProvider::new();
        provider.load_from_data(include_str!("../assets/style.css"));
        gtk4::style_context_add_provider_for_display(&display, &provider, gtk4::STYLE_PROVIDER_PRIORITY_APPLICATION);
    }

    let window = ApplicationWindow::new(app);
    window.set_title(Some("HX32 Download Manager"));
    window.set_default_size(1100, 760);

    let header = HeaderBar::new();
    header.set_show_title_buttons(true);
    let title = Label::new(Some("HX32 Download Manager"));
    title.add_css_class("header-title");
    header.pack_start(&title);
    window.set_titlebar(Some(&header));

    let root = GtkBox::new(Orientation::Vertical, 18);
    root.set_margin_start(12);
    root.set_margin_end(12);
    root.set_margin_top(12);
    root.set_margin_bottom(12);

    let app_state = Rc::new(AppState {
        tasks: RefCell::new(Vec::new()),
        next_id: Cell::new(1),
    });

    let top_panel = build_top_panel(app_state.clone());
    root.append(&top_panel);
    window.set_child(Some(&root));
    window.show();
}

fn build_top_panel(app_state: Rc<AppState>) -> GtkBox {
    let container = GtkBox::new(Orientation::Vertical, 16);
    container.add_css_class("top-toolbar");

    let title = Label::new(Some("HX32 : Téléchargez mieux"));
    title.add_css_class("title-label");
    title.set_wrap(true);
    title.set_xalign(0.0);

    let subtitle = Label::new(Some("Ajoutez une URL, lancez le téléchargement et suivez l’avancement avec une interface claire."));
    subtitle.add_css_class("subtitle-label");
    subtitle.set_wrap(true);
    subtitle.set_xalign(0.0);

    let action_row = GtkBox::new(Orientation::Horizontal, 10);
    action_row.set_halign(gtk4::Align::Fill);

    let url_entry = Entry::new();
    url_entry.set_placeholder_text(Some("Entrez l'URL du fichier à télécharger"));
    url_entry.add_css_class("entry-field");
    url_entry.set_hexpand(true);

    let add_button = Button::with_label("+ Nouveau téléchargement");
    add_button.add_css_class("primary-button");

    action_row.append(&url_entry);
    action_row.append(&add_button);

    container.append(&title);
    container.append(&subtitle);
    container.append(&action_row);

    let list_box = ListBox::new();
    list_box.set_selection_mode(SelectionMode::Single);
    list_box.add_css_class("download-list");
    list_box.set_vexpand(true);

    let scrolled = ScrolledWindow::new();
    scrolled.set_child(Some(&list_box));
    scrolled.set_vexpand(true);
    scrolled.set_min_content_width(540);

    let (details_panel, details_widgets) = build_details_panel();
    let details_widgets = Rc::new(details_widgets);

    let dashboard = GtkBox::new(Orientation::Horizontal, 18);
    dashboard.set_hexpand(true);
    dashboard.append(&scrolled);
    dashboard.append(&details_panel);

    container.append(&dashboard);

    let app_state_clone = app_state.clone();
    let details_widgets_clone = details_widgets.clone();
    list_box.connect_row_selected(move |_, row| {
        if let Some(row) = row {
            let index = row.index();
            if index >= 0 {
                let index = index as usize;
                if let Some(task) = app_state_clone.tasks.borrow().get(index) {
                    update_details(&details_widgets_clone, task);
                }
            }
        }
    });

    let url_entry_clone = url_entry.clone();
    let list_box_clone = list_box.clone();
    let app_state_clone = app_state.clone();
    let add_task = move || {
        let url = url_entry_clone.text().trim().to_string();
        if url.is_empty() {
            return;
        }

        let id = app_state_clone.next_id.get();
        app_state_clone.next_id.set(id + 1);

        let file_name = extract_file_name(&url, id);
        let progress_bar = ProgressBar::new();
        progress_bar.add_css_class("download-progress");

        let status_label = Label::new(Some("En attente"));
        status_label.add_css_class("status-label");
        status_label.set_xalign(0.0);

        let action_button = Button::with_label("Annuler");
        action_button.add_css_class("secondary-button");

        let task_row = create_download_row(&file_name, &progress_bar, &status_label, &action_button);

        let task = DownloadTask {
            id,
            url: url.clone(),
            file_name: file_name.clone(),
            progress: 0.0,
            canceled: false,
            progress_bar: progress_bar.clone(),
            status_label: status_label.clone(),
            action_button: action_button.clone(),
        };

        app_state_clone.tasks.borrow_mut().push(task);
        list_box_clone.append(&task_row);
        url_entry_clone.set_text("");

        let tasks_clone = app_state_clone.tasks.clone();
        action_button.connect_clicked(move |_| {
            let mut tasks = tasks_clone.borrow_mut();
            if let Some(task) = tasks.iter_mut().find(|task| task.id == id) {
                if task.progress < 1.0 {
                    task.canceled = true;
                    task.status_label.set_text("Annulé");
                    task.action_button.set_label("Supprimé");
                    task.action_button.set_sensitive(false);
                }
            }
        });

        start_download_simulation(id, app_state_clone.clone());
    };

    add_button.connect_clicked(move |_| add_task());
    url_entry.connect_activate(move |_| add_task());

    container
}

fn build_details_panel() -> (GtkBox, DetailsWidgets) {
    let details = GtkBox::new(Orientation::Vertical, 18);
    details.add_css_class("details-card");
    details.set_hexpand(true);
    details.set_vexpand(true);

    let details_title = Label::new(Some("Détails du téléchargement"));
    details_title.add_css_class("details-title");
    details_title.set_xalign(0.0);

    let description = Label::new(Some("Sélectionnez une tâche dans la liste pour afficher le chemin, l’état et la progression."));
    description.set_wrap(true);
    description.set_xalign(0.0);
    description.add_css_class("details-text");

    let status_label = Label::new(Some("Statut : —"));
    status_label.set_xalign(0.0);
    status_label.add_css_class("details-text");

    let url_label = Label::new(Some("URL : —"));
    url_label.set_wrap(true);
    url_label.set_xalign(0.0);
    url_label.add_css_class("details-text");

    let details_progress = ProgressBar::new();
    details_progress.add_css_class("details-progress");
    details_progress.set_hexpand(true);

    details.append(&details_title);
    details.append(&description);
    details.append(&status_label);
    details.append(&url_label);
    details.append(&details_progress);

    (
        details,
        DetailsWidgets {
            status: status_label,
            url: url_label,
            progress: details_progress,
        },
    )
}

fn create_download_row(file_name: &str, progress_bar: &ProgressBar, status_label: &Label, action_button: &Button) -> ListBoxRow {
    let row = ListBoxRow::new();
    row.add_css_class("download-row");

    let row_box = GtkBox::new(Orientation::Vertical, 12);
    row_box.set_margin_start(14);
    row_box.set_margin_end(14);
    row_box.set_margin_top(14);
    row_box.set_margin_bottom(14);

    let header = GtkBox::new(Orientation::Horizontal, 16);
    header.set_halign(gtk4::Align::Fill);

    let file_label = Label::new(Some(file_name));
    file_label.add_css_class("download-name");
    file_label.set_xalign(0.0);
    file_label.set_hexpand(true);

    header.append(&file_label);
    header.append(action_button);

    row_box.append(&header);
    row_box.append(progress_bar);
    row_box.append(status_label);

    row.set_child(Some(&row_box));
    row
}

fn update_details(details: &DetailsWidgets, task: &DownloadTask) {
    let status_text = if task.canceled {
        "Annulé"
    } else if task.progress >= 1.0 {
        "Terminé"
    } else {
        "En cours"
    };

    details.status.set_text(&format!("Statut : {}", status_text));
    details.url.set_text(&format!("URL : {}", task.url));
    details.progress.set_fraction(task.progress);
}

fn start_download_simulation(task_id: u32, app_state: Rc<AppState>) {
    glib::timeout_add_local(std::time::Duration::from_millis(120), move || {
        let mut tasks = app_state.tasks.borrow_mut();
        if let Some(task) = tasks.iter_mut().find(|task| task.id == task_id) {
            if task.canceled || task.progress >= 1.0 {
                return Continue(false);
            }

            task.progress += 0.02;
            if task.progress >= 1.0 {
                task.progress = 1.0;
                task.progress_bar.set_fraction(1.0);
                task.status_label.set_text("Téléchargement terminé");
                task.action_button.set_label("Terminé");
                task.action_button.set_sensitive(false);
                return Continue(false);
            }

            task.progress_bar.set_fraction(task.progress);
            task.status_label.set_text(&format!("En cours — {}%", (task.progress * 100.0).round() as i32));
            Continue(true)
        } else {
            Continue(false)
        }
    });
}

fn extract_file_name(url: &str, id: u32) -> String {
    let cleaned = url.split('?').next().unwrap_or(url);
    let candidate = cleaned.rsplit('/').find(|segment| !segment.is_empty()).unwrap_or("fichier");
    if candidate.contains('.') {
        candidate.to_string()
    } else {
        format!("{}-{}.bin", candidate, id)
    }
}
