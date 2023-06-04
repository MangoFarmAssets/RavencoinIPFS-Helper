import os
import sys
import threading
import magic
import platform
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import ImageTk
import qrcode
import pyperclip
from ipfs_wrapper import IPFSWrapper


"""IPFS helper app by @MangoFarmAssets."""


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)


class Application:

    def __init__(self):
        self.root = TkinterDnD.Tk()
        self.root.title("RavencoinIPFS Helper by @Mango Farm")
        self.root.geometry("550x550")
        self.root.resizable(False, False)
        self.ipfs_status_timer = None  # Initiate IPFS timer

        # Icon
        self.root.iconbitmap(resource_path("rvn.ico"))

        # Initialize IPFS wrapper
        self.ipfs = IPFSWrapper()
        self.ipfs_hash = None

        # Create widgets after initializing self.ipfs
        self.create_widgets()

        # Start IPFS timer
        self.start_ipfs_status_timer()

        # Enable TkinterDnD after creating the widgets
        self.root.drop_target_register(DND_FILES)
        self.root.dnd_bind("<<Drop>>", self.handle_dnd)

        # Check IPFS status when script is launched
        self.update_ipfs_status()

    def create_widgets(self):
        self.bg_color = "#0E316E"
        self.canvas = tk.Canvas(self.root, bg="#0E316E", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Initialize IPFS status label
        self.ipfs_status_label = tk.Label(self.root, text="", font=("Arial", 12), bg=self.bg_color, fg="#D3D3D3")
        self.ipfs_status_label.place(x=430, y=515)

        # IPFS click area
        self.drop_image = tk.PhotoImage(file=resource_path("rvn_ipfs.png"))
        w, h = self.drop_image.width(), self.drop_image.height()
        box_size = (350, 350)
        if w > h:
            wpercent = box_size[0] / float(w)
            hsize = int((float(h) * float(wpercent)))
            self.drop_image = self.drop_image.subsample(
                int(w / box_size[0]), int(h / hsize)
            )
        else:
            hpercent = box_size[1] / float(h)
            wsize = int((float(w) * float(hpercent)))
            self.drop_image = self.drop_image.subsample(
                int(w / wsize), int(h / box_size[1])
            )

        # Header text
        self.upload_text = tk.Label(
            self.canvas,
            text="Drag & Drop or Click to Upload",
            font=("TkDefaultFont", 20),
            fg="#D3D3D3",
            bg="#0E316E",
            bd=0,
            pady=0,
        )
        self.upload_text.pack(side=tk.TOP, pady=10)

        self.drop_label = tk.Label(
            self.canvas, image=self.drop_image, bg="#0E316E", padx=10, pady=10
        )
        self.drop_label.pack(side=tk.TOP, anchor=tk.CENTER)

        # Hand on hover
        def on_enter(event):
            self.root.config(cursor="hand2")

        def on_leave(event):
            self.root.config(cursor="")

        self.drop_label.bind("<Enter>", on_enter)
        self.drop_label.bind("<Leave>", on_leave)
        self.drop_label.bind("<Button-1>", self.handle_file_click)

        # Hamburger menu
        self.menu_button = tk.Button(
            self.canvas,
            text="☰",
            command=self.show_menu,
            bg="#0E316E",
            fg="#D3D3D3",
            font=("TkDefaultFont", 14, "bold"),
            pady=10,
            relief=tk.RAISED,
            bd=2,
        )

        # Hamburger placement
        self.menu_button.place(relx=0.97, rely=0.03, width=40, height=30, anchor=tk.NE)

        # Initialize menu
        self.menu = tk.Menu(self.root, tearoff=0)
        self.menu.add_command(label="Home", command=self.reset_window)

        # Hamburger Items
        self.menu.add_command(label="Start IPFS", command=self.start_ipfs)
        self.menu.add_command(label="Stop IPFS", command=self.stop_ipfs)
        self.menu.add_command(label="View File From Hash", command=self.view_hash_window)
        self.menu.add_command(label="Backup to RavencoinIPFS", command=self.backup_ipfs)

        # Bind menu to button
        self.menu_button.bind("<Button-3>", self.show_menu)

        # Create a frame to hold the buttons
        self.button_frame = tk.Frame(self.canvas, bg=self.bg_color)
        self.button_frame.pack(side=tk.BOTTOM, pady=10)

        # Initiate back button
        self.back_button = tk.Button(
            self.button_frame,
            text="Back",
            command=self.reset_window,
            bg="#0E316E",
            fg="#D3D3D3",
            font=("TkDefaultFont", 14, "bold"),
            pady=10,
            relief=tk.RAISED,
            bd=2,
        )
        self.back_button.pack(side=tk.LEFT, padx=10)

        # Initiate copy button
        self.copy_button = tk.Button(
            self.button_frame,
            text="Copy",
            command=self.copy_to_clipboard,
            bg="#0E316E",
            fg="#D3D3D3",
            font=("TkDefaultFont", 14, "bold"),
            pady=10,
            relief=tk.RAISED,
            bd=2,
        )
        self.copy_button.pack(side=tk.LEFT, padx=10)

        # Initiate view button
        self.view_button = tk.Button(
            self.button_frame,
            text="View",
            command=self.button_view_file,
            bg="#0E316E",
            fg="#D3D3D3",
            font=("TkDefaultFont", 14, "bold"),
            pady=10,
            relief=tk.RAISED,
            bd=2,
        )
        self.view_button.pack(side=tk.LEFT, padx=10)

        # Initially hide back, copy, and view buttons
        self.button_frame.pack_forget()

    def backup_ipfs(self):
        messagebox.showerror("Coming soon", "One-Click backup to RavencoinIPFS is coming soon")

    def button_view_file(self):
        # Define the ipfs hash and cat the file from the wrapper
        ipfs_hash = self.ipfs_hash
        file_bytes = self.ipfs.cat_file(ipfs_hash)
        self.view_file(file_bytes)

    def copy_to_clipboard(self):
        hash = self.ipfs_hash
        pyperclip.copy(hash)

    def display_file_hash(self, ipfs_hash):

        # Remove any existing IPFS hash label
        if hasattr(self, "ipfs_hash_label"):
            self.ipfs_hash_label.pack_forget()

        # Create a new frame for the hash and QR code
        hash_frame = tk.Frame(self.canvas, bg=self.bg_color)
        hash_frame.pack(side=tk.TOP, pady=0)

        # Generate the QR code image
        qr_img = self.generate_qr_code_image(ipfs_hash)

        # Check if the image was generated correctly
        if qr_img is None:
            messagebox.showerror("QR Code Error", "Failed to generate QR code image")
            return

        # Create a PhotoImage object from the PIL image object
        img_tk = ImageTk.PhotoImage(qr_img)

        # Create a label to hold the QR code image
        qr_label = tk.Label(hash_frame, image=img_tk, bg=self.bg_color, anchor="center")
        qr_label.image = img_tk  # Store a reference to the image to prevent garbage collection
        qr_label.pack(side=tk.TOP, padx=20)

        # Add the IPFS hash label
        hash_label = tk.Label(
            hash_frame,
            text=f"{ipfs_hash}",
            fg="#FFFFFF",
            bg=self.bg_color,
            font=("TkDefaultFont", 10),
            pady=10,
        )
        hash_label.pack(side=tk.TOP)

        # Store the IPFS hash
        self.ipfs_hash = ipfs_hash

        # Store a reference to the IPFS hash label
        self.ipfs_hash_label = hash_frame

    def gateway_view_file(self):
        # Define the ipfs hash from the text box and cat the file from the wrapper
        ipfs_hash = self.ipfs_hash_entry.get()
        file_bytes = self.ipfs.cat_file(ipfs_hash)
        self.view_file(file_bytes)

    def view_file(self, file_bytes):
        if file_bytes is not None:
            # Get the file type
            file_type = magic.from_buffer(file_bytes.getvalue(), mime=True)
            # special case MIME type to extension mapping
            type_extension_mapping = {
                "application/vnd.ms-excel": "xls",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": "xlsx",
                "application/vnd.ms-powerpoint": "ppt",
                "application/vnd.openxmlformats-officedocument.presentationml.presentation": "pptx",
                "text/plain": "txt",
                "application/rtf": "rtf",
                "text/rtf": "rtf",
                "text/csv": "csv",
                "application/vnd.ms-outlook": "msg",
                "application/json": "json",
                "application/xml": "xml",
                "text/xml": "xml",
                "application/vnd.oasis.opendocument.text": "odt",
                "application/vnd.oasis.opendocument.spreadsheet": "ods",
                "application/vnd.oasis.opendocument.presentation": "odp",
                "image/bmp": "bmp",
                "image/gif": "gif",
                "image/x-icon": "ico",
                "image/svg+xml": "svg",
                "image/tiff": "tif",
                "audio/mpeg": "mp3",
                "video/mp4": "mp4",
                "application/zip": "zip",
                "application/x-rar-compressed": "rar",
                "text/html": "html",
                # Add more mappings as needed in the future
            }

            # Get the extension from the MIME type
            extension = type_extension_mapping.get(file_type, file_type.split('/')[-1])

            # Save the file to a temporary location
            with tempfile.NamedTemporaryFile(delete=False, suffix='.' + extension) as temp_file:
                temp_file.write(file_bytes.getvalue())

            try:
                # Open the file using the appropriate application
                if platform.system() == 'Windows':
                    os.startfile(temp_file.name)
                elif platform.system() == 'Darwin':  # MacOS
                    subprocess.call(('open', temp_file.name))
                else:  # linux variants
                    subprocess.call(('xdg-open', temp_file.name))
            except Exception as e:
                messagebox.showerror("Error:", "File failed to open: " + str(e))

        else:
            messagebox.showerror("Error:", "Failed to retrieve file from IPFS.")

    def generate_qr_code_image(self, ipfs_hash):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=12,
            border=1.5,
        )
        qr.add_data(ipfs_hash)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        return img

    def handle_dnd(self, event):
        file_path = event.data
        if isinstance(file_path, tuple):
            file_path = file_path[0]
        if file_path:
            file_path = file_path.rstrip("}")  # Remove trailing } character if present
            if file_path[0] == "{":
                file_path = file_path[1:]  # Remove leading { character if present
            self.show_file_name(file_path)

    def handle_file_click(self, event):  # User click handling
        file_path = filedialog.askopenfilename()
        if file_path:
            self.show_file_name(file_path)

    def pin_file(self, file_path):
        # Convert the Windows-style file path to a Unix-style file path
        file_path_unix = file_path.replace('\\', '/')

        # Check if IPFS daemon is running
        if not self.ipfs.get_status():
            messagebox.showerror("IPFS Error", "IPFS daemon is not running")
            return None

        # Add the file to IPFS
        try:
            ipfs_hash = self.ipfs.add(file_path_unix)
        except Exception as e:
            messagebox.showerror("IPFS Error", f"Failed to add file to IPFS: {e}")
            return None

        # Pin the IPFS hash
        try:
            self.ipfs.pin_add(ipfs_hash)
        except Exception as e:
            messagebox.showerror("IPFS Error", f"Failed to pin IPFS hash: {e}")
            return None
        return ipfs_hash

    def pin_file_and_display(self, file_path):
        ipfs_hash = self.pin_file(file_path)
        self.root.after(0, self.display_file_hash, ipfs_hash)

    def reset_window(self):  # Reset window to its initial state
        # Reset widgets
        self.upload_text.config(
            text="Drag & Drop or Click to Upload",
            fg="#D3D3D3",
            bg="#0E316E",
            font=("TkDefaultFont", 20),
        )
        self.drop_label.pack(side=tk.TOP, anchor=tk.CENTER)

        # Hide back, copy, and view buttons
        self.button_frame.pack_forget()

        # Show IPFS status label
        self.ipfs_status_label.place(x=430, y=515)

        # Remove IPFS hash label if present
        if hasattr(self, "ipfs_hash_label"):
            self.ipfs_hash_label.pack_forget()

    def show_file_name(self, file_path):
        self.drop_label.pack_forget()
        file_name = os.path.basename(file_path.rstrip("}"))
        self.upload_text.config(
            text=f"Selected file: {file_name}",
            fg="#FFFFFF",
            bg="#0E316E",
            font=("TkDefaultFont", 16),
            pady=10,
        )

        # Pin file and display file hash in a separate thread
        threading.Thread(target=self.pin_file_and_display, args=(file_path,)).start()

        # Show buttons
        self.button_frame.pack(side=tk.BOTTOM, pady=10)

        # Hide IPFS status label
        self.ipfs_status_label.place_forget()

    def show_menu(self, event=None):
        try:
            self.menu.tk_popup(
                self.menu_button.winfo_rootx(), self.menu_button.winfo_rooty()
            )
        finally:
            self.menu.grab_release()

    def start_ipfs(self):
        self.ipfs.start_daemon()
        self.update_ipfs_status()  # Call immediately
        self.start_ipfs_status_timer()  # Start IPFS status timer

    def start_ipfs_status_timer(self):  # Starts the IPFS status timer.
        self.stop_ipfs_status_timer()  # Stop any previous timer

        # Call update_ipfs_status() once every second for ten seconds
        self.ipfs_status_timer = self.root.after(1000, self.update_ipfs_status)
        for i in range(1, 10):
            self.root.after(i * 1000, self.update_ipfs_status)

        # Call update_ipfs_status() once every two minutes after the initial ten seconds
        for i in range(11, 300, 2):
            self.root.after(i * 1000, self.update_ipfs_status)

    def stop_ipfs(self):
        self.ipfs.stop_daemon()
        self.update_ipfs_status()  # Call immediately
        self.stop_ipfs_status_timer()  # Stop IPFS status timer

    def stop_ipfs_status_timer(self):
        if self.ipfs_status_timer is not None:
            self.root.after_cancel(self.ipfs_status_timer)
            self.ipfs_status_timer = None

    def update_ipfs_status(self):
        status_text = self.ipfs.get_status()
        self.ipfs_status_label.config(text=status_text)

    def hide_ipfs(self):
        self.ipfs_status_label.place_forget()

    def view_hash_window(self):
        # Create a new window
        self.ipfs_hash_window = tk.Toplevel(self.root)
        self.ipfs_hash_window.title("IPFS File Gateway")
        self.ipfs_hash_window.geometry("400x200")
        self.ipfs_hash_window.iconbitmap(resource_path("rvn.ico"))

        # Add a label and an entry box
        tk.Label(
            self.ipfs_hash_window,
            text="Copy IPFS Hash",
            font=("TkDefaultFont", 14),
            fg="#0E316E"
        ).pack(pady=20)
        self.ipfs_hash_entry = tk.Entry(
            self.ipfs_hash_window,
            font=("TkDefaultFont", 10),
            fg="#0E316E",
            width=52
        )
        self.ipfs_hash_entry.pack(pady=10)
        self.ipfs_hash_entry.focus_set()

        # Add a view button
        gateway_view_button = tk.Button(
            self.ipfs_hash_window,
            text="View",
            font=("TkDefaultFont", 14),
            fg="#0E316E",
            command=self.gateway_view_file,
            anchor="center"
        )
        gateway_view_button.pack(pady=20)

        # Create an instance of IPFSWrapper
        self.ipfs_wrapper = IPFSWrapper()

        # Bind the Enter key to the gateway_view_file method
        self.ipfs_hash_window.bind("<Return>", self.gateway_view_file)

    def quit(self):
        self.ipfs.stop_daemon()
        self.root.destroy()

    def __del__(self):
        self.ipfs.stop_daemon()

    def run(self):
        try:
            self.ipfs.start_daemon()
            self.root.protocol("WM_DELETE_WINDOW", self.quit)
            self.root.mainloop()
        except:
            self.ipfs.stop_daemon()
            raise


if __name__ == "__main__":
    app = Application()
    try:
        app.run()
    finally:
        del app
