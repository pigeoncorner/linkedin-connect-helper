import customtkinter as ctk
import pyperclip
from PIL import Image
import os
import sys
import ctypes
import threading
import time

# === Configuration ===
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")
global clipboard_thread
clipboard_thread = None

# === Constants ===
TEMPLATE_FILENAME = "li_helper_cache.txt"
ICON_FILENAME = "logo_circle.ico"
START_IMAGE = "logo_start_400.png"
STOP_IMAGE = "logo_stop_400.png"
WINDOW_SIZE = "540x500"
APP_TITLE = "LinkedIn Connect Helper"

DEFAULT_TEMPLATE = (
    "Hi {name},\n"
    "I’m currently expanding my professional network and would appreciate the opportunity to connect with you."
)

# === Template Load/Save ===
def load_template_from_disk():
    if os.path.exists(TEMPLATE_FILENAME):
        with open(TEMPLATE_FILENAME, "r", encoding="utf-8") as f:
            return f.read().strip()
    return DEFAULT_TEMPLATE

def save_template_to_disk(content):
    try:
        ctypes.windll.kernel32.SetFileAttributesW(TEMPLATE_FILENAME, 0x80)  # FILE_ATTRIBUTE_NORMAL
    except Exception:
        pass

    with open(TEMPLATE_FILENAME, "w", encoding="utf-8") as f:
        f.write(content.strip())

    if sys.platform.startswith("win"):
        try:
            FILE_ATTRIBUTE_HIDDEN = 0x02
            ctypes.windll.kernel32.SetFileAttributesW(TEMPLATE_FILENAME, FILE_ATTRIBUTE_HIDDEN)
        except Exception as e:
            print(f"Could not hide template file: {e}")

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller .exe """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# === Main App ===
def main():
    global script_running, message_input

    script_running = False

    app = ctk.CTk()
    app.geometry(WINDOW_SIZE)
    app.title(APP_TITLE)

    # Set window icon
    icon_path = resource_path(ICON_FILENAME)
    if os.path.exists(icon_path):
        app.iconbitmap(icon_path)
    else:
        print(f"Icon not found: {icon_path}")

    # === Images ===
    light_img_raw = Image.open(resource_path(START_IMAGE)).resize((400, 400))
    dark_img_raw = Image.open(resource_path(STOP_IMAGE)).resize((400, 400))
    light_img = ctk.CTkImage(light_img_raw, size=(100, 100))
    dark_img = ctk.CTkImage(dark_img_raw, size=(100, 100))

    # === Image Button and Status ===
    frame = ctk.CTkFrame(app, fg_color="transparent")
    frame.pack(pady=10)

    image_label = ctk.CTkLabel(frame, image=light_img, text="")
    image_label.pack()
    image_label.bind("<Button-1>", lambda e: toggle_script(image_label, status_label, light_img, dark_img))

    status_label = ctk.CTkLabel(frame, text="Script Idle", font=ctk.CTkFont(size=14))
    status_label.pack(pady=(10, 0))

    # === Template and Instructions ===
    template_frame = ctk.CTkFrame(app, fg_color="transparent")
    template_frame.pack(pady=(20, 0))

    ctk.CTkLabel(template_frame,
        text="Template (adjust it as needed, but keep {name}):",
        font=ctk.CTkFont(size=14, weight="bold"),
        width=480,
        anchor="w"
    ).pack()

    message_input = ctk.CTkTextbox(template_frame, width=480, height=100, corner_radius=10, wrap='word')
    message_input.pack(pady=(5, 20))
    message_input.insert("1.0", load_template_from_disk())

    ctk.CTkLabel(template_frame,
        text="Instructions:",
        font=ctk.CTkFont(size=14, weight="bold"),
        width=480,
        anchor="w"
    ).pack()

    instructions_text = (
        "- adjust template as needed, press Start\n"
        "- go to LinkedIn, highlight person’s name,\n"
        "- press Ctrl+C (at this moment script does its job)\n"
        "- click Connect->'Add a note' on LinkedIn,\n"
        "- press Ctrl+V (updated text will be pasted)\n"
        "- when finished, return and press Stop to halt the script"
    )

    ctk.CTkLabel(template_frame,
        text=instructions_text,
        font=ctk.CTkFont(size=12),
        justify="left",
        width=480,
        anchor="w"
    ).pack(pady=(5, 20), fill="x")

    # === Save and Exit ===
    def on_close():
        current_template = message_input.get("1.0", "end").strip()
        save_template_to_disk(current_template)
        app.destroy()

    app.protocol("WM_DELETE_WINDOW", on_close)
    app.mainloop()

# === Script Toggle ===
def toggle_script(image_label, status_label, light_img, dark_img):
    global script_running, clipboard_thread
    script_running = not script_running

    status_label.configure(
        text="✅ Script Running" if script_running else "⏹️ Script Stopped",
        text_color="red" if script_running else "black"
    )
    image_label.configure(image=dark_img if script_running else light_img)

    if script_running:
        clipboard_thread = threading.Thread(target=clipboard_watcher, daemon=True)
        clipboard_thread.start()

def clipboard_watcher():
    global script_running
    last_value = pyperclip.paste()

    try:
        while script_running:
            time.sleep(0.5)
            current_value = pyperclip.paste()
            template = message_input.get("1.0", "end").strip()

            if current_value != last_value and not current_value.startswith("Hi ") and len(current_value) < 100:
                name = current_value.strip()
                if name:
                    formatted = template.format(name=name)
                    pyperclip.copy(formatted)
                    print(f"✅ Message copied to clipboard for: {name}")
                    last_value = formatted
            else:
                last_value = current_value
    except Exception as e:
        print(f"⚠️ Clipboard watcher error: {e}")

# === Entry Point ===
if __name__ == "__main__":
    main()
