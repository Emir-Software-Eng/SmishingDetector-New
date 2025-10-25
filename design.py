import customtkinter as ctk
import json
import builtins
import os

SETTINGS_FILE = "user_settings.json"
PLACEHOLDER_TEXT = "Type here..."


# ===== Load & Save Persistent Settings =====
def load_user_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_user_settings(data):
    try:
        with open(SETTINGS_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print("Settings save error:", e)


def build_ui():
    # ===== Load previous settings =====
    settings = load_user_settings()
    last_font_size = settings.get("font_size", 13)
    last_theme = settings.get("theme", "System")
    auto_save = settings.get("auto_save", "off")

    # ===== Theme & Root =====
    ctk.set_appearance_mode(last_theme.lower())
    ctk.set_default_color_theme("blue")

    root = ctk.CTk()
    root.title("🕵🏽 Smishing / Spam / Legit Detector")
    root.geometry("1000x600")
    root.minsize(880, 550)

    # ===== Tab Control =====
    tabs = ctk.CTkTabview(
        root,
        corner_radius=18,
        fg_color=("#2b2b2b", "#1f1f1f"),
        segmented_button_fg_color=("#3a3a3a", "#292929"),
        segmented_button_selected_color=("#1e88e5", "#1565c0"),
        segmented_button_selected_hover_color=("#2196f3", "#1976d2"),
        segmented_button_unselected_color=("#4a4a4a", "#3a3a3a"),
        segmented_button_unselected_hover_color=("#5a5a5a", "#4a4a4a"),
        text_color=("#ffffff", "#e0e0e0"),
        height=80,
    )
    tabs._segmented_button.configure(
        font=ctk.CTkFont(size=16, weight="bold"),
        height=42,
        corner_radius=12,
    )
    tabs.pack(fill="both", expand=True, padx=15, pady=(20, 15))

    detect_tab = tabs.add("Detect")
    log_tab = tabs.add("Anatomy")
    settings_tab = tabs.add("Settings")

    for tab in (detect_tab, log_tab, settings_tab):
        tab.pack_propagate(False)
        tab.grid_propagate(False)

    # ============================================================== #
    #                      DETECT TAB                                #
    # ============================================================== #
    detect_container = ctk.CTkFrame(detect_tab, corner_radius=10)
    detect_container.pack(fill="both", expand=True, padx=10, pady=10)

    left_frame = ctk.CTkFrame(detect_container, corner_radius=12)
    left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

    right_frame = ctk.CTkFrame(detect_container, width=240, corner_radius=12)
    right_frame.pack(side="right", fill="y", pady=10)

    # ===== SMS Input =====
    title_label = ctk.CTkLabel(
        left_frame, text="💬 SMS BOX",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    title_label.pack(anchor="w", pady=(10, 5), padx=10)

    input_box = ctk.CTkTextbox(
        left_frame, height=100, corner_radius=10,
        font=ctk.CTkFont("Consolas", last_font_size),
    )
    input_box.pack(fill="x", padx=10, pady=(0, 10))
    input_box.insert("1.0", PLACEHOLDER_TEXT)

    def on_focus_in(_):
        if input_box.get("1.0", "end-1c") == PLACEHOLDER_TEXT:
            input_box.delete("1.0", "end")

    def on_focus_out(_):
        if not input_box.get("1.0", "end-1c").strip():
            input_box.insert("1.0", PLACEHOLDER_TEXT)

    input_box.bind("<FocusIn>", on_focus_in)
    input_box.bind("<FocusOut>", on_focus_out)

    # ===== Button Builder =====
    def make_button(parent, text, color, icon=""):
        btn = ctk.CTkButton(
            parent,
            text=f"{icon} {text}".strip(),
            fg_color=color,
            hover_color=color,
            width=190,
            height=38,
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
        )
        btn.pack(pady=5)
        return btn

    # ===== Buttons / Headings =====
    ra_label = ctk.CTkLabel(
        right_frame, text="RUN ANALYSIS",
        font=ctk.CTkFont(size=14, weight="bold"), text_color="#00b0ff",
    )
    ra_label.pack(anchor="w", padx=10, pady=(12, 6))

    predict_btn = make_button(right_frame, "Predict SMS", "#4A8B5D", "▶")
    clear_btn = make_button(right_frame, "Clear Input", "#A94B4B", "🗑")
    load_image_btn = make_button(right_frame, "Load Image/OCR", "#4E7CA1", "🖼")

    nc_label = ctk.CTkLabel(
        right_frame, text="NETWORK CONTROL",
        font=ctk.CTkFont(size=14, weight="bold"), text_color="#00b0ff",
    )
    nc_label.pack(anchor="w", padx=10, pady=(14, 6))

    manage_server_btn = make_button(right_frame, "Manage Server", "#6C5B8D", "🌐")
    network_toggle_btn = make_button(right_frame, "Toggle Network", "#C27A3F", "🔌")

    # ===== Detected =====
    log_results_label = ctk.CTkLabel(
        left_frame, text="🔍 DETECTED",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    log_results_label.pack(anchor="w", padx=10, pady=(8, 3))

    log_results_hint = ctk.CTkLabel(
        left_frame, text="Detected messages (Double-click to view message):",
        font=ctk.CTkFont(size=12),
    )
    log_results_hint.pack(anchor="w", padx=10, pady=(0, 3))

    filter_var = ctk.StringVar(value="All")
    filter_menu = ctk.CTkOptionMenu(
        left_frame, variable=filter_var,
        values=["All", "Smishing", "Spam", "Legit"],
        width=130,
    )
    filter_menu.pack(anchor="w", padx=10, pady=(0, 5))

    # ===== Scrollable Log List (cards) =====
    log_box = ctk.CTkScrollableFrame(left_frame, height=200, corner_radius=10)
    log_box.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    _log_label_widgets = []
    _log_entries = []

    builtins._shared_log_entries = _log_entries  # ✅ Shared across modules

    # ================================================================
    #              CLICKABLE LOG MESSAGE BOX CREATOR
    # ================================================================
    def add_log_message(label, full_text, color, entry_data=None):
        if entry_data:
            _log_entries.append(entry_data)
            entry_index = len(_log_entries) - 1
        else:
            entry_index = None

        preview_line = full_text.split("\n")[0].strip()
        if len(preview_line) > 80:
            preview_line = preview_line[:77] + "..."

        frame = ctk.CTkFrame(log_box, corner_radius=8, fg_color=("#D8D8D8", "#2A2A2A"))
        frame.pack(fill="x", padx=5, pady=3)

        preview_label = ctk.CTkLabel(
            frame,
            text=f"[{label}] {preview_line}",
            text_color=color,
            font=ctk.CTkFont("Consolas", last_font_size),
            anchor="w",
            justify="left",
            padx=6,
        )
        preview_label.pack(fill="x", padx=8, pady=6)

        _log_label_widgets.append(preview_label)
        preview_label.full_message = full_text

        # --- Selection Highlight Logic ---
        selected_colors = {"light": "#B0D8FF", "dark": "#1E3A5F"}
        normal_color = ("#D8D8D8", "#2A2A2A")

        import builtins
        if not hasattr(builtins, "_selected_frame"):
            builtins._selected_frame = None

        def on_select(_event=None):
            try:
                if builtins._selected_frame and builtins._selected_frame.winfo_exists():
                    builtins._selected_frame.configure(fg_color=normal_color)
                from customtkinter import get_appearance_mode
                mode = get_appearance_mode().lower()
                frame.configure(fg_color=selected_colors["dark" if mode == "dark" else "light"])
                builtins._selected_frame = frame
            except Exception:
                pass

        frame.bind("<Button-1>", on_select)
        preview_label.bind("<Button-1>", on_select)

        # =====================================================
        # --- Right-Click Context Menu with Actions ---
        # =====================================================
        # =====================================================
        # --- Right-Click Context Menu with Actions ---
        # =====================================================
        import tkinter as tk
        from tkinter import filedialog, messagebox

        context_menu = tk.Menu(frame, tearoff=0)

        def save_single_log():
            try:
                entry = entry_data or {"message": preview_label.full_message, "label": label}
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text Files", "*.txt")],
                    title="Save Log Entry"
                )
                if save_path:
                    with open(save_path, "w", encoding="utf-8") as f:
                        f.write(f"[{entry.get('label', label)}]\n\n")
                        f.write(entry.get("message", preview_label.full_message))
                        warnings = entry.get("warnings", [])
                        if warnings:
                            f.write("\n\nDetected Features:\n")
                            for w in warnings:
                                f.write(f"• {w}\n")
                    messagebox.showinfo("Saved", f"Log saved successfully:\n{save_path}")
            except Exception as e:
                messagebox.showerror("Save Error", str(e))

        def append_log():
            try:
                entry = entry_data or {"message": preview_label.full_message, "label": label}
                with open("combined_logs.txt", "a", encoding="utf-8") as f:
                    f.write(f"\n\n--- LOG ENTRY ---\n[{entry.get('label', label)}]\n\n")
                    f.write(entry.get("message", preview_label.full_message))
                    warnings = entry.get("warnings", [])
                    if warnings:
                        f.write("\n\nDetected Features:\n")
                        for w in warnings:
                            f.write(f"• {w}\n")
                messagebox.showinfo("Appended", "Log entry added to combined_logs.txt")
            except Exception as e:
                messagebox.showerror("Append Error", str(e))

        def delete_log():
            """Completely remove this log from UI and global memory."""
            try:
                frame.destroy()
                if entry_data:
                    # Remove from this tab’s local list
                    if entry_data in _log_entries:
                        _log_entries.remove(entry_data)

                    # Remove from shared global reference
                    if hasattr(builtins, "_shared_log_entries") and entry_data in builtins._shared_log_entries:
                        builtins._shared_log_entries.remove(entry_data)

                    # Remove from message_store in app.py if exists
                    if hasattr(builtins, "message_store") and entry_data in builtins.message_store:
                        builtins.message_store.remove(entry_data)

                messagebox.showinfo("Deleted", "Log entry deleted successfully.")
            except Exception as e:
                messagebox.showerror("Delete Error", str(e))

        context_menu.add_command(label="💾 Save Log (Single)", command=save_single_log)
        context_menu.add_command(label="📚 Append to Combined Log", command=append_log)
        context_menu.add_separator()
        context_menu.add_command(label="🗑 Delete Log", command=delete_log)

        def show_context_menu(event):
            try:
                on_select()
                frame.focus_set()
                context_menu.tk_popup(event.x_root, event.y_root)
            finally:
                context_menu.grab_release()

        frame.bind("<Button-3>", show_context_menu)
        preview_label.bind("<Button-3>", show_context_menu)
        root.bind_all("<Button-3>", lambda e: None, add="+")


        # --- Double-click logic ---
        def on_double_click(_event, tag=label, widget=preview_label, idx=entry_index):
            tabs.set("Anatomy")
            details_text.config(state="normal")
            details_text.delete("1.0", "end")

            if idx is not None and idx < len(_log_entries):
                entry = _log_entries[idx]
                msg = entry.get("message", widget.full_message)
                warnings = entry.get("warnings", [])
                entry_label = entry.get("label", tag)

                label_lower = entry_label.lower()
                if label_lower == "smishing":
                    icon, label_tag = "🚨", "red_label"
                elif label_lower == "spam":
                    icon, label_tag = "⚠️", "yellow_label"
                elif label_lower == "legit":
                    icon, label_tag = "✅", "green_label"
                elif label_lower == "error":
                    icon, label_tag = "❌", "red_label"
                else:
                    icon, label_tag = "ℹ️", "gray_label"

                details_text.insert("end", " CLASSIFICATION ", "header_classification")
                details_text.insert("end", "\n\n")
                details_text.insert("end", f"{icon} {entry_label}", label_tag)
                details_text.insert("end", "\n\n\n")

                details_text.insert("end", " MESSAGE ", "header_message")
                details_text.insert("end", "\n\n")
                details_text.insert("end", msg)
                details_text.insert("end", "\n\n\n")

                if warnings:
                    details_text.insert("end", " DETECTED FEATURES ", "header_features")
                    details_text.insert("end", "\n\n")
                    for w in warnings:
                        details_text.insert("end", f"• {w}", "warning")
                        details_text.insert("end", "\n")
                else:
                    details_text.insert("end", " STATUS ", "header_status")
                    details_text.insert("end", "\n\n")
                    details_text.insert("end", "✅ No suspicious features detected", "safe")
            else:
                msg = widget.full_message
                details_text.insert("end", " MESSAGE ", "header_message")
                details_text.insert("end", "\n\n")
                details_text.insert("end", msg)

            details_text.config(state="disabled")

        preview_label.bind("<Double-Button-1>", on_double_click)
        frame.bind("<Double-Button-1>", on_double_click)

        return frame

    # ============================================================== #
    #                      LOG DETAILS TAB                           #
    # ============================================================== #
    log_frame = ctk.CTkFrame(log_tab, corner_radius=10)
    log_frame.pack(fill="both", expand=True, padx=10, pady=10)

    log_label = ctk.CTkLabel(
        log_frame, text="📖 Details",
        font=ctk.CTkFont(size=18, weight="bold"),
    )
    log_label.pack(anchor="w", padx=10, pady=(10, 5))

    # Use regular Tkinter Text widget for color support
    import tkinter as tk

    details_text_frame = ctk.CTkFrame(log_frame, corner_radius=10)
    details_text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    details_text = tk.Text(
        details_text_frame,
        height=520,
        wrap="word",
        font=("Consolas", last_font_size),
        bg="#FFFFFF",
        fg="#1A1A1A",
        insertbackground="#1A1A1A",
        relief="flat",
        padx=10,
        pady=10,
        borderwidth=0,
    )
    details_text.pack(fill="both", expand=True, padx=2, pady=2)

    # Configure color tags for the text widget
    details_text.tag_config("red_label", foreground="#ff4d4d", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("yellow_label", foreground="#ffcc00", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("green_label", foreground="#4caf50", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("gray_label", foreground="#808080", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("warning", foreground="#ff6b6b")
    details_text.tag_config("safe", foreground="#4caf50", font=("Consolas", last_font_size, "bold"))

    # Header background colors (like the detected cards)
    details_text.tag_config("header_classification", background="#3a3a3a", foreground="#ffffff", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("header_message", background="#3a3a3a", foreground="#ffffff", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("header_features", background="#3a3a3a", foreground="#ffffff", font=("Consolas", last_font_size, "bold"))
    details_text.tag_config("header_status", background="#3a3a3a", foreground="#ffffff", font=("Consolas", last_font_size, "bold"))

    # ============================================================== #
    #                      SETTINGS TAB                              #
    # ============================================================== #
    settings_frame = ctk.CTkFrame(settings_tab, corner_radius=10)
    settings_frame.pack(fill="both", expand=True, padx=10, pady=10)

    center_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
    center_frame.place(relx=0.5, rely=0.5, anchor="center")

    ctk.CTkLabel(
        center_frame, text="⚙️ Settings",
        font=ctk.CTkFont(size=20, weight="bold"),
    ).pack(pady=(0, 15))

    # Theme selector
    theme_var = ctk.StringVar(value=last_theme)
    ctk.CTkLabel(center_frame, text="Theme Mode:",
                 font=ctk.CTkFont(size=13)).pack(pady=(5, 2))
    theme_menu = ctk.CTkOptionMenu(center_frame, variable=theme_var,
                                   values=["Light", "Dark", "System"], width=160)
    theme_menu.pack(pady=(0, 10))

    # Font size
    font_size_var = ctk.IntVar(value=last_font_size)
    ctk.CTkLabel(center_frame, text="Font Size:",
                 font=ctk.CTkFont(size=13)).pack(pady=(5, 2))
    font_slider = ctk.CTkSlider(center_frame, from_=8, to=30,
                                variable=font_size_var, number_of_steps=22, width=200)
    font_slider.pack(pady=(0, 15))

    # Auto Save
    auto_save_var = ctk.StringVar(value=auto_save)
    auto_save_switch = ctk.CTkSwitch(center_frame, text="Enable Auto Save",
                                     onvalue="on", offvalue="off",
                                     variable=auto_save_var)
    auto_save_switch.pack(pady=(5, 15))

    # ============================================================== #
    #                      STATUS BAR                                #
    # ============================================================== #
    status_bar = ctk.CTkLabel(root, text="Ready", anchor="w",
                              font=ctk.CTkFont(size=12), height=26)
    status_bar.pack(fill="x", side="bottom", padx=10, pady=(0, 5))

    # ================== Theme / Font Updaters ================== #
    def _apply_palette(mode: str):
        """
        Paints all widgets using a compact light/dark palette.
        Ensures: SMS box text color == Log results text color in that theme.
        """
        palettes = {
            "dark":  {"bg": "#0E0E0E", "frame": "#1A1A1A", "inner": "#222222", "text": "#EAEAEA"},
            "light": {"bg": "#FAFAFA", "frame": "#EFEFEF", "inner": "#FFFFFF", "text": "#1A1A1A"},
        }
        C = palettes["dark" if mode == "dark" else "light"]

        # Root + status
        root.configure(fg_color=C["bg"])
        status_bar.configure(fg_color=C["bg"], text_color=C["text"])

        # Tabview internals (best-effort)
        try:
            tabs.configure(fg_color=C["frame"])
            if hasattr(tabs, "_border_frame"):
                tabs._border_frame.configure(fg_color=C["bg"])
            if hasattr(tabs, "_top_frame"):
                tabs._top_frame.configure(fg_color=C["frame"])
            if hasattr(tabs, "_segmented_button"):
                tabs._segmented_button.configure(
                    fg_color=C["frame"],
                    selected_color=("#1e88e5" if mode == "dark" else "#1976D2"),
                    selected_hover_color=("#2196f3" if mode == "dark" else "#1E88E5"),
                    unselected_color=("#3d3d3d" if mode == "dark" else "#D0D0D0"),
                    unselected_hover_color=("#4a4a4a" if mode == "dark" else "#C0C0C0"),
                    text_color=C["text"],
                )
        except Exception:
            pass

        # Frames
        for f in [
            detect_tab, log_tab, settings_tab,
            detect_container, left_frame, right_frame,
            log_frame, settings_frame, center_frame,
        ]:
            f.configure(fg_color=C["frame"])

        # Scrollable frame body & inner frame
        log_box.configure(fg_color=C["inner"])
        # Different CTk versions name the inner container differently:
        for attr in ("scrollable_frame", "_scrollable_frame", "_frame"):  # best-effort coverage
            inner = getattr(log_box, attr, None)
            if inner:
                inner.configure(fg_color=C["inner"])

        # Textboxes share text color (details_text is now tk.Text, skip it in loop)
        input_box.configure(fg_color=C["inner"], text_color=C["text"])
        filter_menu.configure(fg_color=C["inner"], text_color=C["text"])

        # Update tk.Text widget (details_text) colors separately
        try:
            details_text.config(bg=C["inner"], fg=C["text"], insertbackground=C["text"])
        except Exception:
            pass

        # General labels use theme text color
        for lbl in [title_label, log_results_label, log_results_hint, log_label]:
            lbl.configure(text_color=C["text"])

        # Section headers stay blue
        for blue_lbl in [ra_label, nc_label]:
            blue_lbl.configure(text_color="#00b0ff")

        # Existing log labels (cards) keep their *status* color
        root.update_idletasks()
        status_bar.configure(text=f"Theme: {theme_var.get()}")

    def refresh_theme():
        """
        Reliable theme switcher for Light / Dark / System.
        When 'System' is selected, we allow CTk to resolve the OS mode
        and then read it back to apply palette.
        """
        choice = theme_var.get().lower()

        def apply_resolved():
            resolved = ctk.get_appearance_mode().lower()
            _apply_palette(resolved)
            settings["theme"] = theme_var.get()
            save_user_settings(settings)
            status_bar.configure(text=f"Theme: {theme_var.get()} ({resolved})")

        if choice == "system":
            ctk.set_appearance_mode("system")
            # Allow a short tick for CTk to resolve OS mode
            root.after(120, apply_resolved)
        else:
            ctk.set_appearance_mode(choice)
            _apply_palette(choice)
            settings["theme"] = theme_var.get()
            save_user_settings(settings)
            status_bar.configure(text=f"Theme: {theme_var.get()}")

    def update_font_size(_=None):
        new_size = int(font_size_var.get())
        # Update CTk textbox
        input_box.configure(font=ctk.CTkFont("Consolas", new_size))
        # Update tk.Text widget
        details_text.config(font=("Consolas", new_size))
        # Update color tags with new font size
        details_text.tag_config("red_label", foreground="#ff4d4d", font=("Consolas", new_size, "bold"))
        details_text.tag_config("yellow_label", foreground="#ffcc00", font=("Consolas", new_size, "bold"))
        details_text.tag_config("green_label", foreground="#4caf50", font=("Consolas", new_size, "bold"))
        details_text.tag_config("gray_label", foreground="#808080", font=("Consolas", new_size, "bold"))
        details_text.tag_config("safe", foreground="#4caf50", font=("Consolas", new_size, "bold"))
        details_text.tag_config("header_classification", background="#3a3a3a", foreground="#ffffff", font=("Consolas", new_size, "bold"))
        details_text.tag_config("header_message", background="#3a3a3a", foreground="#ffffff", font=("Consolas", new_size, "bold"))
        details_text.tag_config("header_features", background="#3a3a3a", foreground="#ffffff", font=("Consolas", new_size, "bold"))
        details_text.tag_config("header_status", background="#3a3a3a", foreground="#ffffff", font=("Consolas", new_size, "bold"))

        # update existing log labels
        for lbl in _log_label_widgets:
            lbl.configure(font=ctk.CTkFont("Consolas", new_size))

        settings["font_size"] = new_size
        save_user_settings(settings)
        status_bar.configure(text=f"Font size: {new_size}")

    def update_auto_save():
        settings["auto_save"] = auto_save_var.get()
        save_user_settings(settings)
        status_bar.configure(text=f"Auto Save: {auto_save_var.get().title()}")

    # Live updates
    font_slider.configure(command=update_font_size)
    theme_menu.configure(command=lambda *_: refresh_theme())
    auto_save_switch.configure(command=update_auto_save)

    # First paint (also fixes initial light/system mismatch)
    root.after(30, refresh_theme)

    # Back-compat aliases
    log_list = log_box
    network_btn = network_toggle_btn

    return {
        "root": root,
        "tabs": tabs,
        "input_box": input_box,
        "predict_btn": predict_btn,
        "clear_btn": clear_btn,
        "load_image_btn": load_image_btn,
        "manage_server_btn": manage_server_btn,
        "network_toggle_btn": network_toggle_btn,
        "network_btn": network_btn,
        "log_box": log_box,
        "log_list": log_box,
        "filter_var": filter_var,
        "filter_menu": filter_menu,
        "details_text": details_text,
        "theme_var": theme_var,
        "font_size_var": font_size_var,
        "auto_save_var": auto_save_var,
        "status_bar": status_bar,
        "add_log_message": add_log_message,
        "log_entries": _log_entries,  # ✅ Added line for app.py access
    }

if __name__ == "__main__":
    ui = build_ui()
    ui["root"].mainloop()
