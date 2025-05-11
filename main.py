import tkinter as tk
from styles import create_main_button, create_main_label
from diem_danh import DiemDanh
from thong_tin import ThongTinFrame
from admin import AdminFrame

class MainApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Hệ thống chấm công")
        self.root.geometry("800x600")
        self.create_widgets()

    def create_widgets(self):
        # Tiêu đề
        title_label = create_main_label(self.root, "HỆ THỐNG CHẤM CÔNG")
        title_label.pack(pady=30)

        # Frame chứa các nút
        button_frame = tk.Frame(self.root)
        button_frame.pack(pady=20)

        # Nút điểm danh
        diem_danh_button = create_main_button(button_frame, "Điểm danh", self.open_diem_danh)
        diem_danh_button.pack(pady=15)

        # Nút thông tin
        thong_tin_button = create_main_button(button_frame, "Thông tin", self.open_thong_tin)
        thong_tin_button.pack(pady=15)

        # Nút admin
        admin_button = create_main_button(button_frame, "Chế độ admin", self.open_admin)
        admin_button.pack(pady=15)

    def open_diem_danh(self):
        self.root.withdraw()  # Ẩn cửa sổ chính
        diem_danh = DiemDanh(self.root, self)
        diem_danh.show()

    def open_thong_tin(self):
        self.root.withdraw()  # Ẩn cửa sổ chính
        thong_tin = ThongTinFrame(self.root, self.root, self)  # Pass parent, main_window, and main_app
        thong_tin.show()

    def open_admin(self):
        self.root.withdraw()  # Ẩn cửa sổ chính
        # Tạo cửa sổ mới cho admin
        admin_window = tk.Toplevel(self.root)
        admin_window.title("Quản lý hệ thống")
        admin_window.geometry("800x600")
        
        # Tạo AdminFrame trong cửa sổ mới
        admin = AdminFrame(admin_window, self.root, self)  # Pass parent, main_window, and main_app
        admin.show()  # Hiển thị frame

    def show(self):
        self.root.deiconify()  # Hiển thị lại cửa sổ chính

if __name__ == "__main__":
    root = tk.Tk()
    app = MainApp(root)
    root.mainloop()