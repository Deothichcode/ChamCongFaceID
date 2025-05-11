import tkinter as tk
from tkinter import ttk, messagebox
from add_employee import AddEmployee
from delete_employee import DeleteEmployee
from search_employee import SearchEmployee
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

class EmployeeManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Quản lý nhân viên", font=("Arial", 16, "bold")).pack(pady=10)

        # Frame chứa các nút chức năng
        button_frame = tk.Frame(self)
        button_frame.pack(pady=10)

        tk.Button(button_frame, text="Thêm nhân viên", command=self.open_add_employee).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Xóa nhân viên", command=self.open_delete_employee).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Tìm kiếm nhân viên", command=self.open_search_employee).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Làm mới", command=self.refresh).pack(side=tk.LEFT, padx=5)

        # Treeview để hiển thị danh sách nhân viên
        self.tree = ttk.Treeview(self, columns=("STT", "Mã NV", "Họ tên", "Ngày sinh", "Giới tính"), show="headings")
        self.tree.heading("STT", text="STT")
        self.tree.heading("Mã NV", text="Mã nhân viên")
        self.tree.heading("Họ tên", text="Họ tên")
        self.tree.heading("Ngày sinh", text="Ngày sinh")
        self.tree.heading("Giới tính", text="Giới tính")
        self.tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Load danh sách nhân viên
        self.load_employees()

        # Nút quay lại
        tk.Button(self, text="Quay lại", command=self.controller.go_back, bg="red", fg="white", width=20).pack(pady=10)

    def load_employees(self):
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
            
        try:
            # Mở kết nối trực tiếp với CSDL sử dụng đường dẫn toàn cục
            print(f"Loading employees from database at: {EMPLOYEE_DB_PATH}")
            conn = sqlite3.connect(EMPLOYEE_DB_PATH)
            cursor = conn.cursor()
            
            # Thực hiện truy vấn
            cursor.execute("SELECT stt, ma_nv, ho_ten, ngay_sinh, gioi_tinh FROM nhanvien ORDER BY stt")
            rows = cursor.fetchall()
            
            # Kiểm tra số lượng dòng trả về
            print(f"Số lượng nhân viên đọc từ CSDL: {len(rows)}")
            
            # Thêm dữ liệu vào treeview
            for row in rows:
                self.tree.insert("", tk.END, values=row)
                
            # Đóng kết nối
            conn.close()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách nhân viên: {str(e)}")
            print(f"Lỗi tải danh sách nhân viên: {str(e)}")

    def open_add_employee(self):
        add_employee = AddEmployee(self, self.controller.employee_db, self.load_employees)
        add_employee.show()

    def open_delete_employee(self):
        delete_employee = DeleteEmployee(self, self.controller.employee_db, self.tree, self.load_employees)
        delete_employee.delete_employee()

    def open_search_employee(self):
        search_employee = SearchEmployee(self, self.controller.employee_db, self.tree)
        search_employee.show()

    def refresh(self):
        # Làm mới danh sách bằng cách gọi trực tiếp load_employees
        print("Làm mới danh sách nhân viên...")
        self.load_employees()