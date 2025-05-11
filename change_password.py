import tkinter as tk
from tkinter import messagebox

class ChangePasswordFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Thay đổi mật khẩu Admin", font=("Arial", 16, "bold")).pack(pady=10)

        tk.Label(self, text="Mật khẩu cũ:").pack(pady=5)
        self.old_password_entry = tk.Entry(self, show="*")
        self.old_password_entry.pack(pady=5)

        tk.Label(self, text="Mật khẩu mới:").pack(pady=5)
        self.new_password_entry = tk.Entry(self, show="*")
        self.new_password_entry.pack(pady=5)

        tk.Button(self, text="Xác nhận", command=self.change_password).pack(pady=20)

        # Nút quay lại
        tk.Button(self, text="Quay lại", command=self.controller.go_back, bg="red", fg="white", width=20).pack(pady=10)

    def change_password(self):
        old_password = self.old_password_entry.get().strip()
        new_password = self.new_password_entry.get().strip()

        if not old_password or not new_password:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ mật khẩu cũ và mới!")
            return

        try:
            cursor = self.controller.admin_db.execute("SELECT password FROM admin WHERE username=?", ("admin",))
            result = cursor.fetchone()
            if result and result[0] == old_password:
                self.controller.admin_db.execute("UPDATE admin SET password=? WHERE username=?", (new_password, "admin"))
                self.controller.admin_db.commit()
                messagebox.showinfo("Thành công", "Đổi mật khẩu thành công!")
                self.controller.show_frame("ManagementFrame")
            else:
                messagebox.showerror("Lỗi", "Mật khẩu cũ không đúng!")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đổi mật khẩu: {str(e)}")