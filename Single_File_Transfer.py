import os
import customtkinter as ctk
from customtkinter import CTkImage
import qrcode
from PIL import Image, ImageTk
import socket
import threading
import http.server
import socketserver
import urllib.parse

class FileShareApp:
    def __init__(self):
        # Set up the main window
        self.root = ctk.CTk()
        self.root.title("Phone File Share")
        self.root.geometry("600x700")

        # Configure the grid
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(3, weight=1)

        # File selection
        self.file_label = ctk.CTkLabel(self.root, text="No file selected")
        self.file_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        self.select_file_button = ctk.CTkButton(
            self.root, 
            text="Select File", 
            command=self.select_file
        )
        self.select_file_button.grid(row=0, column=1, padx=20, pady=10)

        # QR Code display
        self.qr_label = ctk.CTkLabel(self.root, text="QR Code will appear here")
        self.qr_label.grid(row=1, column=0, columnspan=2, padx=20, pady=10)

        # Generate QR Code button
        self.generate_qr_button = ctk.CTkButton(
            self.root, 
            text="Generate QR Code", 
            command=self.generate_qr_code,
            state="disabled"
        )
        self.generate_qr_button.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

        # Status label
        self.status_label = ctk.CTkLabel(self.root, text="")
        self.status_label.grid(row=4, column=0, columnspan=2, padx=20, pady=10)

        # Selected file path
        self.selected_file_path = None

        # Server variables
        self.server_thread = None
        self.server_port = None
        self.serving_directory = None

    def select_file(self):
        """Open file dialog to select a file for sharing"""
        file_path = ctk.filedialog.askopenfilename()
        if file_path:
            self.selected_file_path = file_path
            self.file_label.configure(text=os.path.basename(file_path))
            self.generate_qr_button.configure(state="normal")

    def get_local_ip(self):
        """Get the local IP address of the computer"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
            return local_ip
        except Exception:
            return "127.0.0.1"

    def start_file_server(self):
        """Start a simple HTTP server to serve the selected file"""
        # Set the serving directory to the directory of the selected file
        self.serving_directory = os.path.dirname(self.selected_file_path)

        class FileHandler(http.server.SimpleHTTPRequestHandler):
            def __init__(self, *args, directory=None, **kwargs):
                super().__init__(*args, directory=directory, **kwargs)

        # Find an available port
        def find_free_port():
            with socketserver.TCPServer(("", 0), FileHandler) as tmp_server:
                return tmp_server.server_address[1]

        self.server_port = find_free_port()

        # Start server in a separate thread
        def run_server():
            os.chdir(self.serving_directory)
            with socketserver.TCPServer(("", self.server_port), FileHandler) as httpd:
                httpd.serve_forever()

        self.server_thread = threading.Thread(target=run_server, daemon=True)
        self.server_thread.start()

    def generate_qr_code(self):
        """Generate QR code for file sharing with URL encoding"""
        if not self.selected_file_path:
            self.status_label.configure(text="Please select a file first")
            return

        # Start the file server
        self.start_file_server()

        # Construct the download URL with URL encoding for special characters
        local_ip = self.get_local_ip()
        file_name = urllib.parse.quote(os.path.basename(self.selected_file_path))
        download_url = f"http://{local_ip}:{self.server_port}/{file_name}"

        # Create QR code
        qr = qrcode.QRCode(
            version=1, 
            box_size=10, 
            border=5
        )
        qr.add_data(download_url)
        qr.make(fit=True)

        # Create an image from the QR code
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to CTkImage for proper scaling
        pil_image = qr_image.resize((300, 300))
        ctk_image = CTkImage(light_image=pil_image, size=(300, 300))

        # Update QR code label
        self.qr_label.configure(image=ctk_image)

        # Update status
        self.status_label.configure(
            text=f"Scan QR Code to download: {download_url}"
        )

    def run(self):
        """Run the application"""
        self.root.mainloop()

def main():
    ctk.set_appearance_mode("system")
    ctk.set_default_color_theme("blue")
    
    app = FileShareApp()
    app.run()

if __name__ == "__main__":
    main()