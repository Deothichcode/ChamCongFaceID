import tkinter as tk
from tkinter import messagebox

class SearchEmployee:
    def __init__(self, parent, employee_db, tree):
        self.parent = parent
        self.db = employee_db  # Sử dụng employee_db
        self.tree = tree
        self.window = None

    def show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Tìm kiếm nhân viên")
        self.window.geometry("400x200")

        tk.Label(self.window, text="Tìm kiếm nhân viên", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Label(self.window, text="Nhập mã nhân viên hoặc họ tên:").pack()
        self.search_entry = tk.Entry(self.window)
        self.search_entry.pack(pady=5)

        tk.Button(self.window, text="Tìm kiếm", command=self.search).pack(pady=20)

    def search(self):
        search_term = self.search_entry.get().strip()
        if not search_term:
            messagebox.showerror("Lỗi", "Vui lòng nhập mã nhân viên hoặc họ tên để tìm kiếm!")
            return

        # Xóa dữ liệu cũ trong Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Tìm kiếm trong database
        query = "SELECT stt, ma_nv, ho_ten, ngay_sinh, gioi_tinh FROM nhanvien WHERE ma_nv LIKE ? OR ho_ten LIKE ?"
        cursor = self.db.execute(query, (f"%{search_term}%", f"%{search_term}%"))
        results = cursor.fetchall()

        if not results:
            messagebox.showinfo("Thông báo", "Không tìm thấy nhân viên nào!")
            return

        # Hiển thị kết quả tìm kiếm
        for row in results:
            self.tree.insert("", tk.END, values=row)

        self.window.destroy()