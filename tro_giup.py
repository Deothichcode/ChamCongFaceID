import tkinter as tk

class TroGiupFrame(tk.Frame):
    def __init__(self, parent, controller):
        super().__init__(parent)
        self.controller = controller

        tk.Label(self, text="Trợ giúp", font=("Arial", 16, "bold")).pack(pady=10)

        # Nút quay lại
        tk.Button(self, text="Quay lại", command=self.controller.go_back, bg="red", fg="white", width=20).pack(pady=10)