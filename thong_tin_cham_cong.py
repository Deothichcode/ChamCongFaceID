import tkinter as tk
from tkinter import ttk
import sqlite3
from datetime import datetime, timedelta
from tkcalendar import Calendar

class ThongTinChamCong:
    def __init__(self, parent):
        self.parent = parent
        self.window = None
        self.tree = None

    def show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Thông tin chấm công")
        self.window.geometry("1000x600")

        # Frame chứa các nút lọc
        filter_frame = tk.Frame(self.window)
        filter_frame.pack(pady=10)

        # Nút lọc theo ngày
        tk.Button(filter_frame, text="Hôm nay", command=lambda: self.filter_by_date("today")).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Tuần này", command=lambda: self.filter_by_date("week")).pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Tháng này", command=lambda: self.filter_by_date("month")).pack(side=tk.LEFT, padx=5)

        # Calendar để chọn ngày cụ thể
        tk.Label(filter_frame, text="Chọn ngày:").pack(side=tk.LEFT, padx=5)
        self.cal = Calendar(filter_frame, selectmode='day', date_pattern='yyyy-mm-dd')
        self.cal.pack(side=tk.LEFT, padx=5)
        tk.Button(filter_frame, text="Lọc theo ngày", command=self.filter_by_selected_date).pack(side=tk.LEFT, padx=5)

        # Tạo Treeview để hiển thị dữ liệu
        columns = ("ID", "Mã NV", "Họ tên", "Thời gian")
        self.tree = ttk.Treeview(self.window, columns=columns, show="headings")
        
        # Đặt tên cột
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=100)
        
        # Thêm thanh cuộn
        scrollbar = ttk.Scrollbar(self.window, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        # Đặt vị trí các widget
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Nút xuất dữ liệu
        export_button = tk.Button(self.window, text="Xuất dữ liệu", command=self.export_data)
        export_button.pack(pady=10)

        # Hiển thị dữ liệu mặc định (hôm nay)
        self.filter_by_date("today")

    def filter_by_date(self, period):
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        
        today = datetime.now().date()
        
        if period == "today":
            query = "SELECT * FROM cham_cong WHERE date(thoi_gian) = ?"
            params = (today.strftime("%Y-%m-%d"),)
        elif period == "week":
            start_of_week = today - timedelta(days=today.weekday())
            query = "SELECT * FROM cham_cong WHERE date(thoi_gian) BETWEEN ? AND ?"
            params = (start_of_week.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        elif period == "month":
            start_of_month = today.replace(day=1)
            query = "SELECT * FROM cham_cong WHERE date(thoi_gian) BETWEEN ? AND ?"
            params = (start_of_month.strftime("%Y-%m-%d"), today.strftime("%Y-%m-%d"))
        
        cursor.execute(query, params)
        self.display_data(cursor.fetchall())
        conn.close()

    def filter_by_selected_date(self):
        selected_date = self.cal.get_date()
        conn = sqlite3.connect('employees.db')
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM cham_cong WHERE date(thoi_gian) = ?", (selected_date,))
        self.display_data(cursor.fetchall())
        conn.close()

    def display_data(self, data):
        # Xóa dữ liệu cũ
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # Thêm dữ liệu mới
        for row in data:
            self.tree.insert("", tk.END, values=row)

    def export_data(self):
        # Lấy dữ liệu từ Treeview
        data = []
        for item in self.tree.get_children():
            data.append(self.tree.item(item)['values'])
        
        # Tạo file CSV
        filename = f"cham_cong_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("ID,Mã NV,Họ tên,Thời gian\n")
            for row in data:
                f.write(','.join(map(str, row)) + '\n')
        
        tk.messagebox.showinfo("Thành công", f"Đã xuất dữ liệu ra file {filename}") 