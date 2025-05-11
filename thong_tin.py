import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta

class ThongTinFrame(tk.Frame):
    def __init__(self, parent, main_window, main_app):
        super().__init__(parent)
        self.main_window = main_window
        self.main_app = main_app  # Lưu reference đến ứng dụng chính
        self.create_widgets()

    def show(self):
        self.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    def create_widgets(self):
        # Tiêu đề
        title_label = tk.Label(self, text="PTIT ATTENDANCE MANAGEMENT", 
                             font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=20)

        # Thông tin phiên bản
        version_label = tk.Label(self, text="Version 0.0.1", 
                               font=("Arial", 12))
        version_label.pack(pady=10)

        # Nút quay lại
        back_button = tk.Button(self, text="Quay lại", 
                              command=self.go_back,
                              width=20, height=2, bg="red", fg="white")
        back_button.pack(pady=20)

    def go_back(self):
        self.destroy()
        self.main_app.show()  # Hiển thị lại giao diện chính