import tkinter as tk
from tkinter import messagebox
import sqlite3
import os
import sys

# Get the absolute path of the parent directory to access the global variables
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the database path from app.py
try:
    from app import EMPLOYEE_DB_PATH
except ImportError:
    # Fallback if import fails
    EMPLOYEE_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "employees.db")
    print(f"Could not import path, using fallback: {EMPLOYEE_DB_PATH}")

class DeleteEmployee:
    def __init__(self, parent, employee_db, tree, refresh_callback):
        self.parent = parent
        self.db_connection = employee_db  # Không sử dụng connection này trực tiếp
        self.tree = tree
        self.refresh_callback = refresh_callback

    def delete_employee(self):
        selected_item = self.tree.selection()
        if not selected_item:
            messagebox.showerror("Lỗi", "Vui lòng chọn một nhân viên để xóa!")
            return

        values = self.tree.item(selected_item)["values"]
        print(f"Selected values: {values}")
        
        # Lấy STT từ dòng được chọn
        stt = values[0]
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc muốn xóa nhân viên với STT {stt}?"):
            try:
                # Thực hiện xóa trực tiếp từ database
                print(f"Connecting to database at: {EMPLOYEE_DB_PATH}")
                conn = sqlite3.connect(EMPLOYEE_DB_PATH)
                cursor = conn.cursor()
                
                # In thông tin trước khi xóa để debug
                cursor.execute("SELECT * FROM nhanvien WHERE stt = ?", (stt,))
                employee_data = cursor.fetchall()
                print(f"Dữ liệu trước khi xóa: {employee_data}")
                
                if not employee_data:
                    messagebox.showerror("Lỗi", f"Không tìm thấy nhân viên với STT {stt}!")
                    conn.close()
                    return
                
                # Thực hiện xóa với tham số chính xác
                cursor.execute("DELETE FROM nhanvien WHERE stt = ?", (stt,))
                
                # Kiểm tra số dòng đã bị xóa
                rows_affected = cursor.rowcount
                print(f"Số dòng bị ảnh hưởng: {rows_affected}")
                
                # Commit thay đổi
                conn.commit()
                
                # Kiểm tra lại sau khi xóa
                cursor.execute("SELECT * FROM nhanvien WHERE stt = ?", (stt,))
                after_delete = cursor.fetchall()
                print(f"Dữ liệu sau khi xóa: {after_delete}")
                
                conn.close()
                
                if rows_affected > 0:
                    messagebox.showinfo("Thành công", "Đã xóa nhân viên thành công!")
                    # Làm mới danh sách
                    print("Gọi hàm refresh_callback để cập nhật giao diện...")
                    self.refresh_callback()
                else:
                    messagebox.showwarning("Cảnh báo", "Nhân viên không bị xóa. Vui lòng thử lại!")
            except Exception as e:
                print(f"Lỗi khi xóa nhân viên: {str(e)}")
                messagebox.showerror("Lỗi", f"Không thể xóa nhân viên: {str(e)}")