import tkinter as tk
from tkinter import messagebox, ttk
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import Calendar
import cv2
# import face_recognition
import numpy as np
from styles import create_label, create_button, create_entry, create_combobox, create_treeview
import os
from add_employee import AddEmployee

class AdminFrame(tk.Frame):
    def __init__(self, parent, main_window, main_app):
        super().__init__(parent)
        self.main_window = main_window
        self.main_app = main_app  # Lưu reference đến ứng dụng chính
        self.create_login_widgets()

    def show(self):
        self.pack(expand=True, fill=tk.BOTH, padx=20, pady=20)

    def create_login_widgets(self):
        # Tiêu đề
        title_label = tk.Label(self, text="ĐĂNG NHẬP QUẢN LÝ", 
                             font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=20)

        # Frame chứa các trường nhập
        input_frame = tk.Frame(self)
        input_frame.pack(pady=10)

        # Trường nhập tên đăng nhập
        tk.Label(input_frame, text="Tên đăng nhập:").grid(row=0, column=0, padx=5, pady=5)
        self.username_entry = tk.Entry(input_frame)
        self.username_entry.grid(row=0, column=1, padx=5, pady=5)

        # Trường nhập mật khẩu
        tk.Label(input_frame, text="Mật khẩu:").grid(row=1, column=0, padx=5, pady=5)
        self.password_entry = tk.Entry(input_frame, show="*")
        self.password_entry.grid(row=1, column=1, padx=5, pady=5)

        # Nút đăng nhập
        login_button = tk.Button(self, text="Đăng nhập", 
                               command=self.login,
                               width=20, height=2, bg="blue", fg="white")
        login_button.pack(pady=10)

        # Nút quay lại
        back_button = tk.Button(self, text="Quay lại", 
                              command=self.go_back,
                              width=20, height=2, bg="red", fg="white")
        back_button.pack(pady=10)

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ thông tin!")
            return

        # Kiểm tra thông tin đăng nhập
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        
        # Tạo bảng admin nếu chưa tồn tại
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS admin (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """)
        
        # Kiểm tra xem có admin nào chưa
        cursor.execute("SELECT COUNT(*) FROM admin")
        if cursor.fetchone()[0] == 0:
            # Nếu chưa có admin, tạo admin mặc định
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
                         ("admin", "admin123"))
            conn.commit()
        
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", (username, password))
        result = cursor.fetchone()
        
        conn.close()

        if result:
            messagebox.showinfo("Thành công", "Đăng nhập thành công!")
            self.create_management_widgets()
        else:
            messagebox.showerror("Lỗi", "Tên đăng nhập hoặc mật khẩu không đúng!")

    def create_management_widgets(self):
        # Xóa các widget đăng nhập
        for widget in self.winfo_children():
            widget.destroy()

        # Tiêu đề
        title_label = tk.Label(self, text="CHẾ ĐỘ ADMIN", 
                             font=("Arial", 16, "bold"), fg="blue")
        title_label.pack(pady=20)

        # Frame chứa các nút
        button_frame = tk.Frame(self)
        button_frame.pack(pady=20)

        # Nút thêm nhân viên
        add_button = tk.Button(button_frame, text="Thêm nhân viên", 
                             command=self.add_employee,
                             width=20, height=2, bg="blue", fg="white")
        add_button.pack(pady=10)

        # Nút xem danh sách nhân viên
        view_button = tk.Button(button_frame, text="Xem danh sách nhân viên", 
                              command=self.view_employees,
                              width=20, height=2, bg="blue", fg="white")
        view_button.pack(pady=10)

        # Nút xem thông tin chấm công
        attendance_button = tk.Button(button_frame, text="Xem thông tin chấm công", 
                                    command=self.view_attendance,
                                    width=20, height=2, bg="blue", fg="white")
        attendance_button.pack(pady=10)

        # Nút quay lại
        back_button = tk.Button(button_frame, text="Quay lại", 
                              command=self.go_back,
                              width=20, height=2, bg="red", fg="white")
        back_button.pack(pady=10)

    def go_back(self):
        self.destroy()
        self.main_app.show()  # Hiển thị lại giao diện chính

    def add_employee(self):
        # Use the fixed AddEmployee class for a more consistent experience
        
        # Create an instance of AddEmployee and show it
        add_employee = AddEmployee(self, self.main_window.employee_db, self.refresh_view)
        add_employee.show()
        
    def refresh_view(self):
        """Refresh any open employee views"""
        # Find any open view windows with employee lists
        for window in self.winfo_children():
            if isinstance(window, tk.Toplevel):
                # Check if this window has a treeview
                for child in window.winfo_children():
                    if isinstance(child, ttk.Treeview):
                        self.load_employees_data(child)
                        print("Refreshed employee view")
                        return
        
        print("No employee views to refresh")

    def view_employees(self):
        # Tạo cửa sổ xem danh sách
        view_window = tk.Toplevel(self)
        view_window.title("Danh sách nhân viên")
        view_window.geometry("1000x700")

        # Frame chứa các chức năng
        function_frame = tk.Frame(view_window)
        function_frame.pack(pady=10, padx=10, fill=tk.X)

        # Frame tìm kiếm
        search_frame = tk.Frame(function_frame)
        search_frame.pack(side=tk.LEFT, padx=10)

        # Label và Entry cho tìm kiếm
        tk.Label(search_frame, text="Nhập ID:", font=("Arial", 12)).pack(side=tk.LEFT, padx=5)
        search_entry = tk.Entry(search_frame, font=("Arial", 12), width=15)
        search_entry.pack(side=tk.LEFT, padx=5)

        # Nút tìm kiếm
        search_button = tk.Button(search_frame, text="Tìm kiếm", 
                                command=lambda: self.search_employee(search_entry.get(), tree),
                                font=("Arial", 12), bg="blue", fg="white")
        search_button.pack(side=tk.LEFT, padx=5)

        # Frame chứa các nút chức năng khác
        button_frame = tk.Frame(function_frame)
        button_frame.pack(side=tk.RIGHT, padx=10)

        # Nút xóa nhân viên
        delete_button = tk.Button(button_frame, text="Xóa nhân viên", 
                                command=lambda: self.delete_employee(tree),
                                font=("Arial", 12), bg="red", fg="white")
        delete_button.pack(side=tk.LEFT, padx=5)

        # Nút cập nhật thông tin
        update_button = tk.Button(button_frame, text="Cập nhật thông tin", 
                                command=lambda: self.update_employee(tree),
                                font=("Arial", 12), bg="green", fg="white")
        update_button.pack(side=tk.LEFT, padx=5)

        # Nút quay lại
        back_button = tk.Button(button_frame, text="Quay lại", 
                              command=view_window.destroy,
                              font=("Arial", 12), bg="red", fg="white")
        back_button.pack(side=tk.LEFT, padx=5)

        # Treeview hiển thị danh sách - thay đổi để phù hợp với cấu trúc bảng
        tree = ttk.Treeview(view_window, columns=("Mã NV", "Họ tên", "Ngày sinh", "Giới tính"), show="headings")
        tree.heading("Mã NV", text="Mã NV")
        tree.heading("Họ tên", text="Họ tên")
        tree.heading("Ngày sinh", text="Ngày sinh")
        tree.heading("Giới tính", text="Giới tính")

        # Đặt độ rộng cho các cột
        tree.column("Mã NV", width=100)
        tree.column("Họ tên", width=200)
        tree.column("Ngày sinh", width=150)
        tree.column("Giới tính", width=100)

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(view_window, orient="vertical", command=tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        tree.configure(yscrollcommand=scrollbar.set)

        # Load dữ liệu ban đầu
        self.load_employees_data(tree)

    def load_employees_data(self, tree):
        # Xóa dữ liệu cũ
        for item in tree.get_children():
            tree.delete(item)

        try:
            # Kết nối database
            conn = sqlite3.connect('employees.db')
            cursor = conn.cursor()

            # Lấy danh sách nhân viên bao gồm cả STT
            cursor.execute("SELECT stt, ma_nv, ho_ten, ngay_sinh, gioi_tinh FROM nhanvien ORDER BY stt")
            employees = cursor.fetchall()
            
            print(f"Number of employees loaded: {len(employees)}")

            # Hiển thị danh sách, bỏ qua cột STT khi hiển thị
            for employee in employees:
                # Chỉ hiển thị từ cột thứ 2 (ma_nv) trở đi
                tree.insert("", tk.END, values=employee[1:], tags=(str(employee[0]),))
                
            # Lưu STT vào tag để có thể truy cập khi cần
            tree.bind("<ButtonRelease-1>", lambda event: self.on_tree_select(event, tree))

            conn.close()
        except Exception as e:
            print(f"Error loading employee list: {str(e)}")
            messagebox.showerror("Error", "Cannot load employee list!")
            
    def on_tree_select(self, event, tree):
        # Lưu STT vào biến global hoặc thuộc tính của class khi cần
        selected_item = tree.selection()
        if selected_item:
            # Lấy tag của item được chọn (chứa STT)
            try:
                item_tags = tree.item(selected_item[0], "tags")
                if item_tags:
                    self.selected_stt = int(item_tags[0])
                    print(f"Đã chọn nhân viên STT: {self.selected_stt}")
            except Exception as e:
                print(f"Lỗi khi lấy STT: {str(e)}")

    def search_employee(self, search_id, tree):
        if not search_id:
            messagebox.showwarning("Cảnh báo", "Vui lòng nhập ID nhân viên cần tìm!")
            return

        # Xóa dữ liệu cũ trong tree
        for item in tree.get_children():
            tree.delete(item)

        # Kết nối database
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()

        # Tìm nhân viên theo ID (đã bỏ sdt và que_quan)
        cursor.execute("""
            SELECT ma_nv, ho_ten, ngay_sinh, gioi_tinh 
            FROM nhanvien 
            WHERE ma_nv = ?
        """, (search_id,))
        employee = cursor.fetchone()

        if employee:
            tree.insert("", tk.END, values=employee)
        else:
            messagebox.showinfo("Thông báo", f"Không tìm thấy nhân viên có ID: {search_id}")
            self.load_employees_data(tree)  # Load lại toàn bộ danh sách

        conn.close()

    def delete_employee(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần xóa!")
            return

        # Lấy STT từ tag của item đã chọn
        stt = int(tree.item(selected_item[0], "tags")[0])
        employee_id = tree.item(selected_item[0])["values"][0]  # Mã NV
        
        if messagebox.askyesno("Xác nhận", f"Bạn có chắc chắn muốn xóa nhân viên {employee_id}?"):
            try:
                # Kết nối database
                conn = sqlite3.connect('employees.db')
                cursor = conn.cursor()
                
                # Xóa nhân viên theo STT (primary key)
                cursor.execute("DELETE FROM nhanvien WHERE stt = ?", (stt,))
                
                # Kiểm tra xem có dòng nào bị xóa không
                if cursor.rowcount > 0:
                    conn.commit()
                    messagebox.showinfo("Thành công", "Đã xóa nhân viên thành công!")
                else:
                    messagebox.showwarning("Cảnh báo", "Không thể xóa nhân viên!")
                    
                conn.close()
                self.load_employees_data(tree)  # Load lại danh sách
            except Exception as e:
                print(f"Lỗi khi xóa nhân viên: {str(e)}")
                messagebox.showerror("Lỗi", f"Không thể xóa nhân viên: {str(e)}")

    def update_employee(self, tree):
        selected_item = tree.selection()
        if not selected_item:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn nhân viên cần cập nhật!")
            return

        # Lấy STT từ tag của item đã chọn
        stt = int(tree.item(selected_item[0], "tags")[0])
        employee_data = tree.item(selected_item[0])['values']  # Dữ liệu hiển thị
        
        # Tạo cửa sổ cập nhật
        update_window = tk.Toplevel()
        update_window.title("Cập nhật thông tin nhân viên")
        update_window.geometry("400x500")

        # Frame chứa các trường nhập
        input_frame = tk.Frame(update_window)
        input_frame.pack(pady=20, padx=20)

        # ID (readonly)
        tk.Label(input_frame, text="Mã nhân viên:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
        id_label = tk.Label(input_frame, text=employee_data[0], font=("Arial", 12))
        id_label.grid(row=0, column=1, sticky="w", pady=5)

        # Họ tên
        tk.Label(input_frame, text="Họ tên:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        name_entry = tk.Entry(input_frame, font=("Arial", 12))
        name_entry.insert(0, employee_data[1])
        name_entry.grid(row=1, column=1, sticky="w", pady=5)

        # Ngày sinh
        tk.Label(input_frame, text="Ngày sinh:", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        dob_entry = tk.Entry(input_frame, font=("Arial", 12))
        dob_entry.insert(0, employee_data[2])
        dob_entry.grid(row=2, column=1, sticky="w", pady=5)

        # Giới tính
        tk.Label(input_frame, text="Giới tính:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
        gender_var = tk.StringVar(value=employee_data[3] if len(employee_data) > 3 else "Nam")
        gender_combo = ttk.Combobox(input_frame, textvariable=gender_var, values=["Nam", "Nữ"], font=("Arial", 12))
        gender_combo.grid(row=3, column=1, sticky="w", pady=5)

        def save_update():
            try:
                # Kết nối database
                conn = sqlite3.connect('employees.db')
                cursor = conn.cursor()
                
                # Cập nhật thông tin sử dụng stt (primary key)
                print(f"Updating employee with STT {stt}")
                cursor.execute("""
                    UPDATE nhanvien 
                    SET ho_ten = ?, ngay_sinh = ?, gioi_tinh = ?
                    WHERE stt = ?
                """, (name_entry.get(), dob_entry.get(), gender_var.get(), stt))
                
                if cursor.rowcount > 0:
                    conn.commit()
                    messagebox.showinfo("Thành công", "Cập nhật thông tin thành công!")
                    update_window.destroy()
                    self.load_employees_data(tree)  # Load lại danh sách
                else:
                    # Có thể không có dòng nào bị ảnh hưởng nếu dữ liệu không thay đổi
                    conn.commit()
                    messagebox.showinfo("Thông báo", "Không có thay đổi nào được thực hiện!")
                    update_window.destroy()
                    self.load_employees_data(tree)
                
                conn.close()
            except Exception as e:
                print(f"Lỗi khi cập nhật nhân viên: {str(e)}")
                messagebox.showerror("Lỗi", f"Không thể cập nhật thông tin: {str(e)}")

        # Nút lưu
        save_button = tk.Button(update_window, text="Lưu thay đổi", 
                              command=save_update,
                              font=("Arial", 12), bg="green", fg="white")
        save_button.pack(pady=20)

        # Nút hủy
        cancel_button = tk.Button(update_window, text="Hủy", 
                                command=update_window.destroy,
                                font=("Arial", 12), bg="red", fg="white")
        cancel_button.pack(pady=10)

    def view_attendance(self):
        # Tạo cửa sổ xem thông tin chấm công
        view_window = tk.Toplevel(self)
        view_window.title("Thông tin chấm công")
        view_window.geometry("800x600")

        # Frame chứa các tùy chọn lọc
        filter_frame = tk.Frame(view_window)
        filter_frame.pack(pady=10)

        # Label và Entry cho mã nhân viên
        tk.Label(filter_frame, text="Mã nhân viên:").grid(row=0, column=0, padx=5)
        self.ma_nv_entry = tk.Entry(filter_frame)
        self.ma_nv_entry.grid(row=0, column=1, padx=5)

        # Label và Combobox cho loại lọc
        tk.Label(filter_frame, text="Lọc theo:").grid(row=0, column=2, padx=5)
        self.filter_var = ttk.Combobox(filter_frame, values=["Ngày", "Tuần", "Tháng"])
        self.filter_var.grid(row=0, column=3, padx=5)
        self.filter_var.current(0)

        # Label và Entry cho ngày
        tk.Label(filter_frame, text="Ngày:").grid(row=0, column=4, padx=5)
        self.date_entry = tk.Entry(filter_frame)
        self.date_entry.grid(row=0, column=5, padx=5)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

        # Nút tìm kiếm
        search_button = tk.Button(filter_frame, text="Tìm kiếm", 
                                command=self.search_attendance,
                                width=10, bg="blue", fg="white")
        search_button.grid(row=0, column=6, padx=5)

        # Nút quay lại
        back_button = tk.Button(filter_frame, text="Quay lại", 
                              command=view_window.destroy,
                              width=10, bg="red", fg="white")
        back_button.grid(row=0, column=7, padx=5)

        # Treeview hiển thị kết quả
        self.attendance_tree = ttk.Treeview(view_window, columns=("STT", "Mã NV", "Họ tên", "Thời gian"), show="headings")
        self.attendance_tree.heading("STT", text="STT")
        self.attendance_tree.heading("Mã NV", text="Mã NV")
        self.attendance_tree.heading("Họ tên", text="Họ tên")
        self.attendance_tree.heading("Thời gian", text="Thời gian")
        self.attendance_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Scrollbar
        scrollbar = ttk.Scrollbar(view_window, orient="vertical", command=self.attendance_tree.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.attendance_tree.configure(yscrollcommand=scrollbar.set)

        # Tải dữ liệu mặc định
        self.search_attendance()

    def search_attendance(self):
        # Xóa dữ liệu cũ
        for item in self.attendance_tree.get_children():
            self.attendance_tree.delete(item)
            
        ma_nv = self.ma_nv_entry.get().strip()
        filter_type = self.filter_var.get()
        date_input = self.date_entry.get().strip()
        
        print(f"Tìm kiếm với: Mã NV={ma_nv}, Filter={filter_type}, Date={date_input}")
        
        # Kiểm tra ngày không được rỗng
        if not date_input:
            messagebox.showerror("Lỗi", "Vui lòng nhập ngày để tìm kiếm")
            return
            
        # Kiểm tra định dạng ngày
        try:
            if filter_type == 'date':
                datetime.strptime(date_input, '%Y-%m-%d')
            # Không cần kiểm tra định dạng cho week và month vì sẽ dùng strftime
        except ValueError:
            messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ. Vui lòng nhập theo định dạng YYYY-MM-DD")
            return
            
        try:
            # Kết nối database
            conn = sqlite3.connect('employees.db')
            cursor = conn.cursor()
            
            # Kiểm tra bảng cham_cong tồn tại
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='cham_cong'")
            if not cursor.fetchone():
                print("Bảng cham_cong không tồn tại")
                messagebox.showinfo("Thông báo", "Chưa có dữ liệu điểm danh nào")
                return
                
            # Xây dựng câu truy vấn SQL dựa trên loại filter
            query = "SELECT ma_nv, ho_ten, thoi_gian FROM cham_cong WHERE 1=1"
            params = []
            
            # Thêm điều kiện mã nhân viên nếu có
            if ma_nv:
                query += " AND ma_nv = ?"
                params.append(ma_nv)
                
            # Thêm điều kiện ngày tháng
            if filter_type == 'date':
                query += " AND date(thoi_gian) = date(?)"
                params.append(date_input)
            elif filter_type == 'week':
                # Tìm kiếm trong khoảng 7 ngày, từ ngày được chọn trở đi
                try:
                    date_obj = datetime.strptime(date_input, '%Y-%m-%d')
                    end_date = date_obj + timedelta(days=6)
                    query += " AND date(thoi_gian) BETWEEN date(?) AND date(?)"
                    params.append(date_input)
                    params.append(end_date.strftime('%Y-%m-%d'))
                except ValueError:
                    messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ")
                    return
            elif filter_type == 'month':
                # Lấy tháng và năm từ ngày nhập vào
                try:
                    date_obj = datetime.strptime(date_input, '%Y-%m-%d')
                    month = date_obj.month
                    year = date_obj.year
                    query += " AND strftime('%m', thoi_gian) = ? AND strftime('%Y', thoi_gian) = ?"
                    params.append(f"{month:02d}")  # Đảm bảo tháng có 2 chữ số
                    params.append(f"{year}")
                except ValueError:
                    messagebox.showerror("Lỗi", "Định dạng ngày không hợp lệ")
                    return
                
            # Thêm sắp xếp theo thời gian giảm dần
            query += " ORDER BY thoi_gian DESC"
            
            print(f"Executing query: {query} with params: {params}")
            
            cursor.execute(query, params)
            results = cursor.fetchall()
            
            # Kiểm tra có kết quả không
            if not results:
                print("Không tìm thấy kết quả phù hợp")
                
                # Kiểm tra xem có dữ liệu nào trong bảng không
                cursor.execute("SELECT COUNT(*) FROM cham_cong")
                total_count = cursor.fetchone()[0]
                
                if total_count > 0:
                    messagebox.showinfo("Thông báo", "Không tìm thấy dữ liệu điểm danh phù hợp với điều kiện")
                    if ma_nv:
                        # Kiểm tra mã nhân viên có tồn tại
                        cursor.execute("SELECT COUNT(*) FROM cham_cong WHERE ma_nv = ?", (ma_nv,))
                        nv_count = cursor.fetchone()[0]
                        if nv_count == 0:
                            messagebox.showinfo("Thông báo", f"Nhân viên có mã '{ma_nv}' chưa có dữ liệu điểm danh nào")
                else:
                    messagebox.showinfo("Thông báo", "Chưa có dữ liệu điểm danh nào trong hệ thống")
                return
                
            # Hiển thị kết quả
            print(f"Tìm thấy {len(results)} kết quả")
            for i, (ma_nv, ho_ten, thoi_gian) in enumerate(results, 1):
                # Định dạng lại thời gian nếu cần
                try:
                    dt = datetime.strptime(thoi_gian, '%Y-%m-%d %H:%M:%S')
                    formatted_time = dt.strftime('%Y-%m-%d %H:%M:%S')
                except ValueError:
                    formatted_time = thoi_gian
                    
                self.attendance_tree.insert("", "end", values=(i, ma_nv, ho_ten, formatted_time))
                
        except Exception as e:
            print(f"Lỗi khi tìm kiếm điểm danh: {str(e)}")
            messagebox.showerror("Lỗi", f"Lỗi khi tìm kiếm dữ liệu: {str(e)}")
        finally:
            if 'conn' in locals() and conn:
                conn.close()
                print("Đã đóng kết nối database sau khi tìm kiếm")