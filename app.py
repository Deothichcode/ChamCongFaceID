import tkinter as tk
import sqlite3
from trang_chu import TrangChu
import os

# Define database paths globally
DB_DIR = os.path.dirname(os.path.abspath(__file__))
ADMIN_DB_PATH = os.path.join(DB_DIR, "admin.db")
EMPLOYEE_DB_PATH = os.path.join(DB_DIR, "employees.db")

print(f"Database directory: {DB_DIR}")
print(f"Admin DB path: {ADMIN_DB_PATH}")
print(f"Employee DB path: {EMPLOYEE_DB_PATH}")

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("ỨNG DỤNG ĐIỂM DANH CHẤM CÔNG PTIT")
        self.geometry("700x550")
        
        # Khởi tạo 2 kết nối database
        self.admin_db = sqlite3.connect(ADMIN_DB_PATH)
        self.employee_db = sqlite3.connect(EMPLOYEE_DB_PATH)
        
        # Đảm bảo bảng nhanvien tồn tại
        self.setup_database()

        # Hiển thị trang chủ
        self.trang_chu = TrangChu(self)
        self.trang_chu.show()
        
    def setup_database(self):
        cursor = self.employee_db.cursor()
        
        # Tạo bảng nhanvien 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nhanvien (
                stt INTEGER PRIMARY KEY,
                ma_nv TEXT UNIQUE NOT NULL,
                ho_ten TEXT NOT NULL,
                ngay_sinh TEXT,
                gioi_tinh TEXT,
                face_image_path TEXT
            )
        """)
        
        # Tạo bảng admin 
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)
        
        # Tạo bảng chấm công nếu chưa tồn tại
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cham_cong (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ma_nv TEXT NOT NULL,
                ho_ten TEXT NOT NULL,
                thoi_gian TEXT NOT NULL
            )
        """)
        
        # Kiểm tra số lượng nhân viên hiện có
        cursor.execute("SELECT COUNT(*) FROM nhanvien")
        employee_count = cursor.fetchone()[0]
        print(f"Current employee count: {employee_count}")
        
        self.employee_db.commit()
        print("Database setup completed successfully")

    def destroy(self):
        # Đóng kết nối database khi thoát
        self.admin_db.close()
        self.employee_db.close()
        super().destroy()

if __name__ == "__main__":
    app = App()
    app.mainloop()