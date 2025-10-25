import os
import sys
import joblib
import builtins
import numpy as np
import tkinter as tk
from tkinter import messagebox, filedialog

# ==== Internal Components ====
from components.preprocess import clean_text
from components.sms_cropper import SMSCropper
from components.feature_extraction import (
    detect_urls, detect_emails, detect_phone_numbers, detect_domains
)
from components.intro_screen import IntroScreen
from components.user_verification import UserVerification
from components.network_sms_receiver import NetworkSMSReceiver, PORT

# ==== UI Builder ====
from design import build_ui


# ================================================================
#                      RESOURCE PATH
# ================================================================
def resource_path(relative_path: str) -> str:
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


# ================================================================
#                      MODEL LOADING
# ================================================================
MODEL_PATH = resource_path("sms_model.joblib")
VECTORIZER_PATH = resource_path("tfidf_vectorizer.joblib")

MODEL = None
VECTORIZER = None

if os.path.exists(MODEL_PATH) and os.path.exists(VECTORIZER_PATH):
    try:
        MODEL = joblib.load(MODEL_PATH)
        VECTORIZER = joblib.load(VECTORIZER_PATH)
    except Exception as e:
        print(f"⚠️ WARNING: Failed to load model bundle:\n{e}")


# ================================================================
#                      GLOBAL STATE
# ================================================================
import builtins
message_store = getattr(builtins, "_shared_log_entries", [])     # Full message data entries
log_widgets = []       # Track visible log widgets for filtering
network_manager = None


# ================================================================
#                      UI HELPERS
# ================================================================
def show_error_popup(title, message):
    messagebox.showerror(title, message)


def clear_input():
    input_box.delete("1.0", "end")


# ================================================================
#                      CONTEXT MENU ACTIONS
# ================================================================
def save_single_log(entry):
    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")],
        title="Save This Log"
    )
    if not path:
        return
    try:
        with open(path, "w", encoding="utf-8") as f:
            f.write(f"[{entry['label']}] {entry['message'] or 'System message'}\n")
            for w in entry.get("warnings", []):
                f.write(f"  {w}\n")
        messagebox.showinfo("Saved", f"Log saved to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save log:\n{e}")


def append_single_log(entry):
    path = "combined_logs.txt"
    try:
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"[{entry['label']}] {entry['message'] or 'System message'}\n")
            for w in entry.get("warnings", []):
                f.write(f"  {w}\n")
            f.write("\n")
        messagebox.showinfo("Saved", f"Appended to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to append log:\n{e}")


def delete_single_log(entry, frame):
    try:
        if entry in message_store:
            message_store.remove(entry)
        frame.destroy()
        log_widgets[:] = [w for w in log_widgets if w["frame"] != frame]
        messagebox.showinfo("Deleted", "Log entry deleted.")
    except ValueError:
        messagebox.showwarning("Warning", "Log entry already removed.")


# ================================================================
#                      LOGGING / DISPLAY
# ================================================================
def apply_filter(*_):
    selected = filter_var.get()
    for w in log_widgets:
        f = w["frame"]
        lbl = w["label"]
        if selected == "All" or lbl.lower() == selected.lower():
            f.pack(fill="x", padx=5, pady=3)
        else:
            f.pack_forget()


def add_log(message, label, warnings_list=None):
    lbl = (label or "Info").lower()
    full_message = message or "System Message"

    color_map = {
        "smishing": "#ff4d4d",
        "spam": "#ffcc00",
        "legit": "#4caf50",
        "error": "#ff4d4d",
        "info": "#e0e0e0",
    }
    color = color_map.get(lbl, "#e0e0e0")

    entry = {"message": message, "label": label, "warnings": warnings_list or []}
    message_store.append(entry)

    frame = add_log_message(label, full_message, color, entry_data=entry)

    # Right-click context menu
    context_menu = tk.Menu(frame, tearoff=0)
    context_menu.add_command(label="💾 Save Log (Single)", command=lambda e=entry: save_single_log(e))
    context_menu.add_command(label="📚 Append to Combined Log", command=lambda e=entry: append_single_log(e))
    context_menu.add_separator()
    context_menu.add_command(label="🗑 Delete Log", command=lambda e=entry, f=frame: delete_single_log(e, f))

    def show_context_menu(event):
        context_menu.tk_popup(event.x_root, event.y_root)

    frame.bind("<Button-3>", show_context_menu)
    log_widgets.append({"frame": frame, "label": label})
    apply_filter()


# ================================================================
#                      PREDICTION LOGIC
# ================================================================
def process_message_for_prediction(text, source="Manual Input"):
    global MODEL, VECTORIZER

    if MODEL is None or VECTORIZER is None:
        show_error_popup("Model Not Loaded", "Please ensure model files exist.")
        return

    try:
        urls = detect_urls(text)
        emails = detect_emails(text)
        phones = detect_phone_numbers(text)
        domains = detect_domains(text)

        cleaned = clean_text(text)
        X = VECTORIZER.transform([cleaned])
        raw_label = MODEL.predict(X)[0] if hasattr(MODEL, "predict") else "error"

        label_map = {0: "ham", 1: "smishing", 2: "spam"}
        raw_label = label_map.get(int(raw_label), str(raw_label))
        display_label = "Legit" if raw_label.lower() == "ham" else raw_label.capitalize()

        if display_label != "Legit" and source == "Manual Input":
            verifier = UserVerification(root, text, display_label)
            display_label = verifier.ask_user()

        warnings = []
        if urls: warnings.append("URLs: " + ", ".join(urls))
        if emails: warnings.append("Emails: " + ", ".join(emails))
        if phones: warnings.append("Phones: " + ", ".join(phones))
        if domains: warnings.append("Domains: " + ", ".join(domains))

        add_log(text, display_label, warnings)

    except Exception as e:
        show_error_popup("Prediction Error", str(e))
        add_log(f"Prediction failed for message from {source}: {e}", "Error")


def predict_action():
    text = input_box.get("1.0", "end").strip()
    if not text or text == "Type here...":
        messagebox.showwarning("Warning", "Please enter a message first.")
        return
    process_message_for_prediction(text)
    clear_input()


# ================================================================
#                      IMAGE OCR INPUT
# ================================================================
def load_image_to_input():
    path = filedialog.askopenfilename(filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])
    if not path:
        return

    def insert_text(t):
        input_box.delete("1.0", "end")
        input_box.insert("end", t)

    SMSCropper(root, path, insert_text)


# ================================================================
#                      NETWORK
# ================================================================
def on_sms_received_callback(message):
    text = message.get("message", "") if isinstance(message, dict) else str(message)
    source = message.get("sender", "Network") if isinstance(message, dict) else "Network"
    if text:
        process_message_for_prediction(text, source)


def toggle_network():
    global network_manager
    if network_manager and getattr(network_manager, "is_running", False):
        network_manager.stop_server()
        network_manager = None
        network_btn.configure(text="Toggle Network (OFF)")
        add_log("Network server stopped.", "Info")
    else:
        network_manager = NetworkSMSReceiver(PORT, on_sms_received_callback)
        network_manager.start_server()
        network_btn.configure(text="Toggle Network (ON)")
        add_log(f"Network server listening on port {PORT}.", "Info")


def manage_server_action():
    messagebox.showinfo("Server Management", "Manage Server button clicked!")


# ================================================================
#                      SAVE / EXIT
# ================================================================
def _save_logs_prompt():
    """Save only unique, active logs from shared memory."""
    import builtins
    global message_store

    # Always pull the live shared list
    if hasattr(builtins, "_shared_log_entries"):
        message_store = builtins._shared_log_entries

    # Filter out empty or invalid entries
    logs_to_save = [d for d in message_store if d and d.get("message")]

    # Deduplicate by (message, label) combo
    unique_logs = []
    seen = set()
    for log in logs_to_save:
        key = (log.get("message"), log.get("label"))
        if key not in seen:
            seen.add(key)
            unique_logs.append(log)

    if not unique_logs:
        return

    path = filedialog.asksaveasfilename(
        defaultextension=".txt",
        filetypes=[("Text Files", "*.txt")],
        title="Save All Logs"
    )
    if not path:
        return

    try:
        with open(path, "w", encoding="utf-8") as f:
            for d in unique_logs:
                f.write(f"[{d['label']}] {d['message'] or 'System message'}\n")
                for w in d.get("warnings", []):
                    f.write(f"    {w}\n")
        messagebox.showinfo("Saved", f"Logs saved to {path}")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to save logs:\n{e}")

def on_closing():
    global network_manager, message_store

    # Sync again before exit
    if hasattr(builtins, "_shared_log_entries"):
        message_store = builtins._shared_log_entries

    active_logs = [d for d in message_store if d and d.get("message")]

    if active_logs:
        res = messagebox.askyesnocancel(
            "Save Logs?", "You have unsaved logs. Save before exit?"
        )
        if res is True:
            _save_logs_prompt()
        elif res is None:
            return

    if network_manager and getattr(network_manager, "is_running", False):
        network_manager.stop_server()

    root.destroy()

# ================================================================
#                      INITIALIZE UI
# ================================================================
ui = build_ui()

root = ui["root"]
input_box = ui["input_box"]
details_text = ui["details_text"]
filter_var = ui["filter_var"]
predict_btn = ui["predict_btn"]
clear_btn = ui["clear_btn"]
load_image_btn = ui["load_image_btn"]
manage_server_btn = ui["manage_server_btn"]
network_btn = ui["network_btn"]
add_log_message = ui["add_log_message"]

# ✅ Sync internal logs to global message_store
if "log_entries" in ui:
    message_store = ui["log_entries"]

predict_btn.configure(command=predict_action)
clear_btn.configure(command=clear_input)
load_image_btn.configure(command=load_image_to_input)
manage_server_btn.configure(command=manage_server_action)
network_btn.configure(command=toggle_network)
filter_var.trace_add("write", apply_filter)

root.protocol("WM_DELETE_WINDOW", on_closing)

# === Intro screen: show splash first, then reveal main UI ===

def show_main_ui():
    """Show the main app window after the intro finishes."""
    root.deiconify()

def start_intro():
    # Create intro and override its close behavior
    intro = IntroScreen(root, duration=3000)

    # When the intro closes, call our function to show the UI
    def on_intro_close():
        intro.root.destroy()
        show_main_ui()

    intro._close = on_intro_close  # safely replace the close method

# Hide the main window first
root.withdraw()

# Start the intro after 100ms delay
root.after(100, start_intro)

root.mainloop()
