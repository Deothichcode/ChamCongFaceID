import tkinter as tk

class ManagementFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Chào mừng đến với chế độ quản lý", font=("Arial", 14, "bold")).pack(pady=20)

        tk.Button(self, text="Quản lý nhân viên", width=20, command=lambda: self.controller.show_frame("EmployeeManagementFrame")).pack(pady=5)
        tk.Button(self, text="Thay đổi mật khẩu Admin", width=20, command=lambda: self.controller.show_frame("ChangePasswordFrame")).pack(pady=5)
        tk.Button(self, text="Đăng xuất", width=20, command=lambda: self.controller.show_frame("MainFrame")).pack(pady=20)

        # Nút quay lại
        tk.Button(self, text="Quay lại", command=self.controller.go_back, bg="red", fg="white", width=20).pack(pady=10)