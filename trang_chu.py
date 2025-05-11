import tkinter as tk
from tkinter import messagebox
from diem_danh import DiemDanh
from thong_tin import ThongTinFrame
from admin import AdminFrame
from styles import create_label, create_button

class TrangChu:
    def __init__(self, parent):
        self.parent = parent
        self.window = parent  # Sử dụng cửa sổ chính
        self.current_frame = None  # Lưu frame hiện tại

    def show(self):
        # Xóa tất cả widget hiện có trong cửa sổ
        for widget in self.window.winfo_children():
            widget.destroy()

        # Tiêu đề
        title_label = create_label(self.window, "ỨNG DỤNG ĐIỂM DANH CHẤM CÔNG PTIT")
        title_label.pack(pady=30)

        # Frame chứa các nút
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)

        # Nút điểm danh
        diem_danh_button = create_button(button_frame, "Điểm danh", self.open_diem_danh)
        diem_danh_button.pack(pady=15)

        # Nút thông tin
        thong_tin_button = create_button(button_frame, "Thông tin", self.open_thong_tin)
        thong_tin_button.pack(pady=15)

        # Nút chế độ admin
        admin_button = create_button(button_frame, "Chế độ Admin", self.open_admin)
        admin_button.pack(pady=15)

    def open_diem_danh(self):
        # Xóa tất cả widget hiện có trong cửa sổ
        for widget in self.window.winfo_children():
            widget.destroy()
        
        # Tạo đối tượng điểm danh và hiển thị
        self.current_diem_danh = DiemDanh(self.window, self)
        self.current_diem_danh.show()

    def open_thong_tin(self):
        # Xóa tất cả widget hiện có trong cửa sổ
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.current_frame = ThongTinFrame(self.window, self.parent, self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)

    def open_admin(self):
        # Xóa tất cả widget hiện có trong cửa sổ
        for widget in self.window.winfo_children():
            widget.destroy()
        
        self.current_frame = AdminFrame(self.window, self.parent, self)
        self.current_frame.pack(fill=tk.BOTH, expand=True)