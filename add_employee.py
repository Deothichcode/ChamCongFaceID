import tkinter as tk
from tkinter import ttk, messagebox
import cv2
import sqlite3
import os
import uuid
import numpy as np
from datetime import datetime
import time
import threading
import sys
import base64
from PIL import Image, ImageTk

class AddEmployee:    
    def __init__(self, parent, db_file, refresh_callback=None):
        self.parent = parent
        self.db_file = db_file  # Database file path
        self.db = None  # Will be initialized when needed
        self.refresh_callback = refresh_callback
        self.window = None
        self.cap = None
        self.is_capturing = False
        self.frame = None
        self.face_image = None
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        self.detection_frames = 0  # Đếm số frame đã phát hiện khuôn mặt
        self.best_frame = None
        self.cam_width = 640
        self.cam_height = 480
        
        # Khởi tạo biến status_var
        self.status_var = tk.StringVar()
        self.status_var.set("Sẵn sàng")
        
        # Khởi tạo các biến khác
        self.camera_thread = None
        
        self.show()
        
    def show(self):
        self.window = tk.Toplevel(self.parent)
        self.window.title("Thêm Nhân Viên Mới") 
        self.window.geometry("800x700")
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
        
        # Đảm bảo thư mục faces tồn tại
        if not os.path.exists("faces"):
            os.makedirs("faces")
            print("Đã tạo thư mục faces")
        
        # Frame chứa các trường thông tin
        info_frame = tk.Frame(self.window)
        info_frame.pack(pady=10, padx=20, fill="x")
        
        # Tạo các trường nhập thông tin
        tk.Label(info_frame, text="Mã nhân viên:", font=("Arial", 12)).grid(row=0, column=0, sticky="w", pady=5)
        self.ma_nv_entry = tk.Entry(info_frame, font=("Arial", 12), width=30)
        self.ma_nv_entry.grid(row=0, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Họ tên:", font=("Arial", 12)).grid(row=1, column=0, sticky="w", pady=5)
        self.ho_ten_entry = tk.Entry(info_frame, font=("Arial", 12), width=30)
        self.ho_ten_entry.grid(row=1, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Ngày sinh (YYYY-MM-DD):", font=("Arial", 12)).grid(row=2, column=0, sticky="w", pady=5)
        self.ngay_sinh_entry = tk.Entry(info_frame, font=("Arial", 12), width=30)
        self.ngay_sinh_entry.grid(row=2, column=1, sticky="w", pady=5)
        
        tk.Label(info_frame, text="Giới tính:", font=("Arial", 12)).grid(row=3, column=0, sticky="w", pady=5)
        self.gender_var = tk.StringVar(value="Nam")
        gender_combo = ttk.Combobox(info_frame, textvariable=self.gender_var, values=["Nam", "Nữ"], font=("Arial", 12), width=28)
        gender_combo.grid(row=3, column=1, sticky="w", pady=5)
        
        # Frame chứa camera và ảnh
        camera_frame = tk.Frame(self.window)
        camera_frame.pack(pady=10, padx=20, fill="both", expand=True)
        
        # Canvas hiển thị camera
        self.camera_canvas = tk.Canvas(camera_frame, width=640, height=480, bg="black")
        self.camera_canvas.pack(side=tk.LEFT, padx=10, pady=10)
        
        # Frame chứa ảnh đã chụp và hướng dẫn
        self.image_frame = tk.Frame(camera_frame)
        self.image_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill="both", expand=True)
        
        # Canvas hiển thị ảnh khuôn mặt đã chụp
        self.face_canvas = tk.Canvas(self.image_frame, width=150, height=150, bg="gray")
        self.face_canvas.pack(pady=10)
        
        # Hiển thị các hướng dẫn chụp ảnh chất lượng
        guide_text = """HƯỚNG DẪN THÊM NHÂN VIÊN:
1. Nhập đầy đủ thông tin nhân viên
2. Nhấn nút "1. Bắt đầu Camera" để kích hoạt camera
3. Đảm bảo khuôn mặt nằm trong khung xanh
4. Nhấn nút "2. Chụp ảnh" khi khuôn mặt hiển thị rõ ràng
5. Nhấn nút "3. Lưu nhân viên" để hoàn tất

LƯU Ý KHI CHỤP ẢNH:
- Ánh sáng đầy đủ, tránh ngược sáng
- Nhìn thẳng vào camera
- Không đeo kính, mũ, khẩu trang
- Giữ nguyên vị trí khi chụp"""
        
        self.guide_label = tk.Label(self.image_frame, text=guide_text, justify="left", font=("Arial", 10, "bold"), fg="blue", bg="#f0f0f0")
        self.guide_label.pack(pady=10, fill="x")
        
        # Hiển thị chất lượng ảnh
        self.quality_var = tk.StringVar(value="Chất lượng: Chưa chụp")
        self.quality_label = tk.Label(self.image_frame, textvariable=self.quality_var, font=("Arial", 12, "bold"))
        self.quality_label.pack(pady=5)
        
        # Thêm nhãn phản hồi
        self.feedback_label = tk.Label(self.image_frame, text="", font=("Arial", 11), fg="black")
        self.feedback_label.pack(pady=5)
        
        # Biến hình ảnh
        self.image_path_var = tk.StringVar(value="")
        
        # Frame chứa các nút
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20, padx=20)
        
        # Frame riêng cho các nút camera
        camera_button_frame = tk.Frame(button_frame)
        camera_button_frame.pack(side=tk.TOP, fill="x", pady=10)
        
        # Nút bật/tắt camera
        self.capture_button = tk.Button(camera_button_frame, text="1. Bắt đầu Camera", 
                                      command=self.toggle_camera,
                                      font=("Arial", 12, "bold"), bg="blue", fg="white", width=15)
        self.capture_button.pack(side=tk.LEFT, padx=10)
        
        # Nút chụp ảnh
        self.capture_button = tk.Button(camera_button_frame, text="2. Chụp ảnh", 
                                      command=self.capture_face,
                                      font=("Arial", 12), bg="blue", fg="white")
        self.capture_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút lưu nhân viên
        self.save_button = tk.Button(camera_button_frame, text="3. Lưu nhân viên", 
                                   command=self.save_employee,
                                   font=("Arial", 12), bg="green", fg="white")
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)
        
        # Nút hủy
        self.cancel_button = tk.Button(save_button_frame, text="Hủy", 
                                     command=self.on_close,
                                     font=("Arial", 12), bg="red", fg="white", width=15)
        self.cancel_button.pack(side=tk.LEFT, padx=10)
        
        # Status label with larger, more visible font and colored background
        status_frame = tk.Frame(self.window, bg="#e6f7ff", bd=2, relief=tk.RAISED)
        status_frame.pack(pady=10, padx=20, fill="x")
        
        self.status_label = tk.Label(status_frame, textvariable=self.status_var, 
                                   font=("Arial", 12, "bold"), bg="#e6f7ff", fg="#0066cc",
                                   wraplength=700, justify="center", padx=10, pady=5)
        self.status_label.pack(fill="x")
        
    def toggle_camera(self):
        """Bật/tắt camera"""
        if not self.is_capturing:
            # Bắt đầu camera
            try:
                # Đảm bảo giải phóng camera cũ nếu có
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
                    self.cap = None
                    print("Đã giải phóng camera cũ")
                
                # Mở camera với DirectShow backend (nhanh hơn trên Windows)
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap.isOpened():
                    self.cap = cv2.VideoCapture(0)  # Thử lại nếu CAP_DSHOW không hoạt động
                
                if not self.cap.isOpened():
                    messagebox.showerror("Lỗi", "Không thể mở camera. Vui lòng kiểm tra lại thiết bị của bạn.")
                    return
                
                # Thiết lập độ phân giải và FPS của camera
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                self.cap.set(cv2.CAP_PROP_FPS, 20)  # Giảm xuống 20 FPS để tránh lag
                
                # Đọc một frame để kiểm tra camera
                ret, test_frame = self.cap.read()
                if not ret or test_frame is None:
                    messagebox.showerror("Lỗi", "Không thể đọc dữ liệu từ camera.")
                    self.cap.release()
                    self.cap = None
                    return
                
                self.is_capturing = True
                self.capture_button.config(text="Tắt Camera", relief=tk.SUNKEN, bg="#ff7675")
                self.status_var.set("Đã bật camera. Bạn có thể chụp ảnh.")
                
                # Tạo và bắt đầu thread xử lý camera
                self.camera_thread = threading.Thread(target=self.camera_thread_function)
                self.camera_thread.daemon = True  # Thread sẽ tự động kết thúc khi chương trình đóng
                self.camera_thread.start()
                print("Đã bắt đầu thread camera")
                            
            except Exception as e:
                messagebox.showerror("Lỗi", f"Lỗi khi khởi động camera: {str(e)}")
                print(f"Lỗi khi khởi động camera: {e}")
                self.is_capturing = False
                if hasattr(self, 'cap') and self.cap is not None:
                    self.cap.release()
                    self.cap = None
        else:
            # Tắt camera
            self.is_capturing = False
            if hasattr(self, 'cap') and self.cap is not None:
                self.cap.release()
                self.cap = None
            
            # Dừng thread nếu đang chạy
            if hasattr(self, 'camera_thread') and self.camera_thread.is_alive():
                print("Đang đợi thread camera kết thúc...")
                # Thread sẽ tự kết thúc khi self.is_capturing = False
                time.sleep(0.5)  # Đợi thread kết thúc
            
            # Reset status
            self.capture_button.config(text="1. Bắt đầu Camera", relief=tk.RAISED, bg="#dfe6e9")
            self.status_var.set("Đã tắt camera. Bấm 'Bắt đầu Camera' để bắt đầu.")
            
            # Xóa ảnh hiển thị nếu có
            if hasattr(self, 'face_canvas') and self.face_canvas:
                self.face_canvas.create_image(0, 0, image="", anchor=tk.NW)
                self.face_canvas.create_text(self.face_canvas.winfo_width()//2, self.face_canvas.winfo_height()//2, 
                                      text="Camera đã tắt", fill="white", font=('Helvetica', 14))
    
    def camera_thread_function(self):
        """Xử lý camera trong một thread riêng biệt"""
        last_time = time.time()
        frames_processed = 0
        
        while self.is_capturing:
            if not hasattr(self, 'cap') or self.cap is None or not self.cap.isOpened():
                print("Camera không khả dụng trong thread")
                break
            
            try:
                # Đọc frame từ camera
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("Không thể đọc frame từ camera trong thread")
                    time.sleep(0.1)
                    continue
                    
                # Lật ngang frame để hiển thị đúng hướng
                frame = cv2.flip(frame, 1)
                
                # Phát hiện khuôn mặt chỉ khi cần
                if frames_processed % 5 == 0:  # Chỉ xử lý mỗi 5 frame để giảm tải
                    # Phát hiện khuôn mặt
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_cascade.detectMultiScale(
                        gray, 
                        scaleFactor=1.1, 
                        minNeighbors=5,
                        minSize=(30, 30)
                    )
                    
                    # Vẽ hình chữ nhật xung quanh khuôn mặt và hiển thị hướng dẫn
                    display_frame = frame.copy()
                    if len(faces) > 0:
                        # Hiển thị chỉ khuôn mặt lớn nhất
                        face = max(faces, key=lambda x: x[2] * x[3])
                        x, y, w, h = face
                        
                        # Vẽ hướng dẫn
                        cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                        
                        # Hiển thị hướng dẫn
                        cv2.putText(display_frame, "Di chuyển khuôn mặt vào giữa", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    else:
                        # Không có khuôn mặt nào được phát hiện
                        cv2.putText(display_frame, "Không phát hiện khuôn mặt", 
                                  (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    display_frame = frame.copy()
                
                # Cập nhật giao diện trong main thread
                self.update_frame_from_thread(display_frame)
                
                # Tính FPS và in ra để debug
                frames_processed += 1
                current_time = time.time()
                if current_time - last_time >= 5.0:  # Báo cáo FPS mỗi 5 giây
                    fps = frames_processed / (current_time - last_time)
                    print(f"Camera FPS: {fps:.2f}")
                    frames_processed = 0
                    last_time = current_time
                    
                # Nghỉ một chút để giảm tải CPU
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Lỗi trong camera thread: {str(e)}")
                time.sleep(0.5)  # Đợi một chút trước khi thử lại
            
        print("Đã kết thúc thread camera")

    def update_frame_from_thread(self, frame):
        """Cập nhật frame từ camera thread sang giao diện chính"""
        if frame is None or not self.is_capturing:
            return
        
        try:
            # Đảm bảo frame có đúng kích thước cho widget
            frame = cv2.resize(frame, (self.cam_width, self.cam_height))
            
            # Chuyển từ BGR sang RGB cho Tkinter
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Chuyển đổi sang định dạng PhotoImage
            image = Image.fromarray(rgb_frame)
            photo = ImageTk.PhotoImage(image=image)
            
            # Lưu trữ tham chiếu để tránh garbage collection
            self.current_photo = photo
            
            # Cập nhật label với ảnh mới
            self.camera_canvas.img = photo
            self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=photo)
            
            # Lưu frame cuối cùng để sử dụng khi chụp ảnh
            self.last_frame = frame.copy()
            
        except Exception as e:
            print(f"Lỗi khi cập nhật frame: {str(e)}")
        
        # Lên lịch gọi phương thức này lần nữa trong main thread
        # (sử dụng after_idle thay vì after để đảm bảo nó chạy khi UI không bận)
    
    def update_camera(self):
        """Cập nhật camera - chuyển sang dùng update_frame"""
        if not self.is_capturing or self.cap is None:
            return
            
        # Đọc frame từ camera
        ret, frame = self.cap.read()
        if not ret or frame is None:
            self.status_var.set("Lỗi đọc camera")
            return
        
        try:
            # Lưu frame hiện tại
            self.frame = frame.copy()
            
            # Xử lý phát hiện khuôn mặt
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            gray = cv2.equalizeHist(gray)
            
            # Phát hiện khuôn mặt
            faces = self.face_cascade.detectMultiScale(
                gray, 
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100),
                flags=cv2.CASCADE_SCALE_IMAGE
            )
            
            # Nếu phát hiện được khuôn mặt
            if len(faces) > 0:
                x, y, w, h = faces[0]  # Lấy khuôn mặt đầu tiên
                
                # Vẽ hình chữ nhật xanh xung quanh khuôn mặt
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Hiển thị hướng dẫn kích thước
                size_text = f"Kich thuoc: {w}x{h} px"
                cv2.putText(frame, size_text, (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                
                # Tăng bộ đếm số frame phát hiện liên tục
                self.detection_frames += 1
                
                # Nếu phát hiện ổn định khuôn mặt (30 frame liên tục) thì lưu ảnh khuôn mặt
                if self.detection_frames >= 30:
                    # Mở rộng vùng nhận diện
                    x_extended = max(0, int(x - 0.1 * w))
                    y_extended = max(0, int(y - 0.1 * h))
                    w_extended = min(frame.shape[1] - x_extended, int(w * 1.2))
                    h_extended = min(frame.shape[0] - y_extended, int(h * 1.2))
                    
                    # Lấy ảnh khuôn mặt mở rộng
                    face_img = frame[y_extended:y_extended+h_extended, x_extended:x_extended+w_extended]
                    
                    # Chuẩn hóa kích thước ảnh khuôn mặt về 150x150
                    face_img = cv2.resize(face_img, (150, 150))
                    
                    # Nâng cao chất lượng ảnh
                    # 1. Áp dụng bộ lọc Gaussian để giảm nhiễu
                    face_img = cv2.GaussianBlur(face_img, (3, 3), 0)
                    
                    # 2. Tăng độ tương phản
                    lab = cv2.cvtColor(face_img, cv2.COLOR_BGR2LAB)
                    l, a, b = cv2.split(lab)
                    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
                    l = clahe.apply(l)
                    lab = cv2.merge((l, a, b))
                    face_img = cv2.cvtColor(lab, cv2.COLOR_LAB2BGR)
                    
                    # Lưu ảnh đã xử lý
                    self.face_image = face_img
                    
                    # Hiển thị ảnh khuôn mặt đã xử lý trên canvas
                    self.display_face_image()
                    
                    # Đánh giá chất lượng ảnh
                    quality_result = self.evaluate_image_quality(face_img)
                    
                    # Hiển thị độ phân giải và chất lượng hình ảnh
                    self.quality_var.set(quality_result if quality_result != "OK" else "Chất lượng: Tốt")
                    
                    # Đổi trạng thái
                    cv2.putText(frame, "DA PHAT HIEN KHUON MAT - CLICK 'CHUP ANH'", (10, frame.shape[0] - 30), 
                            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)
            else:
                # Reset bộ đếm nếu không phát hiện khuôn mặt
                self.detection_frames = 0
                cv2.putText(frame, "KHONG PHAT HIEN KHUON MAT", (10, frame.shape[0] - 30), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
            
            # Sử dụng phương thức update_frame để hiển thị frame
            self.update_frame(frame)
            
            # Lập lịch cập nhật frame tiếp theo
            self.window.after(30, self.update_camera)
            
        except Exception as e:
            self.status_var.set(f"Lỗi cập nhật camera: {str(e)}")
            print(f"Lỗi cập nhật camera: {e}")
            self.window.after(100, self.update_camera)
    
    def evaluate_image_quality(self, frame):
        """Đánh giá chất lượng ảnh khuôn mặt"""
        if frame is None:
            return "Không thể đọc dữ liệu từ camera"
        
        # Chuyển đổi sang ảnh xám
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Kiểm tra độ sáng
        brightness = np.mean(gray)
        if brightness < 40:
            return "Ảnh quá tối, vui lòng điều chỉnh ánh sáng"
        if brightness > 200:
            return "Ảnh quá sáng, vui lòng giảm ánh sáng"
        
        # Kiểm tra độ tương phản
        contrast = np.std(gray)
        if contrast < 20:
            return "Ảnh thiếu độ tương phản, vui lòng điều chỉnh ánh sáng"
        
        # Phát hiện khuôn mặt bằng Haar Cascade
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            return "Không phát hiện khuôn mặt trong ảnh"
        
        if len(faces) > 1:
            return "Phát hiện nhiều khuôn mặt, vui lòng chỉ để một người trong khung hình"
        
        # Kiểm tra kích thước khuôn mặt
        x, y, w, h = faces[0]
        face_size = w * h
        frame_area = frame.shape[0] * frame.shape[1]
        face_ratio = face_size / frame_area
        
        if face_ratio < 0.05:
            return "Khuôn mặt quá nhỏ, vui lòng di chuyển gần camera hơn"
        
        if face_ratio > 0.7:
            return "Khuôn mặt quá gần, vui lòng di chuyển xa camera hơn"
        
        # Kiểm tra độ mờ
        laplacian_var = cv2.Laplacian(gray[y:y+h, x:x+w], cv2.CV_64F).var()
        if laplacian_var < 50:
            return "Ảnh bị mờ, vui lòng giữ camera ổn định"
        
        # Hiển thị khung khuôn mặt và thông báo chất lượng
        self.face_frame = frame.copy()
        cv2.rectangle(self.face_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
        self.face_frame = self.display_quality_feedback(self.face_frame, "Khuôn mặt đã được phát hiện, chất lượng tốt", "success")
        
        return "OK"
    
    def display_face_image(self):
        if self.face_image is None:
            return
        
        try:
            # Chuyển sang RGB để hiển thị
            face_rgb = cv2.cvtColor(self.face_image, cv2.COLOR_BGR2RGB)
            
            # Tạo encoding ppm để hiển thị trong Tkinter
            _, enc_img = cv2.imencode('.ppm', face_rgb)
            img_bytes = enc_img.tobytes()
            
            # Hiển thị trên canvas
            img = tk.PhotoImage(data=img_bytes)
            self.face_canvas.img = img  # Giữ tham chiếu
            self.face_canvas.create_image(0, 0, anchor=tk.NW, image=img)
        except Exception as e:
            print(f"Lỗi khi hiển thị ảnh khuôn mặt: {e}")
    
    def recapture(self):
        # Reset ảnh khuôn mặt
        self.face_image = None
        self.detection_frames = 0
        self.quality_var.set("Chất lượng: Chưa chụp")
        
        # Nếu camera đang chạy, chỉ cần reset trạng thái
        if self.is_capturing:
            self.capture_button.config(state=tk.DISABLED)
            self.status_var.set("Camera đang sẵn sàng, vui lòng chụp ảnh khi đã sẵn sàng")
        else:
            # Nếu camera đã tắt, bật lại camera
            self.toggle_camera()
        
        # Vô hiệu hóa nút chụp lại
        self.capture_button.config(state=tk.DISABLED)
    
    def save_employee(self):
        # Lấy thông tin từ form
        ma_nv = self.ma_nv_entry.get().strip()
        ho_ten = self.ho_ten_entry.get().strip()
        ngay_sinh = self.ngay_sinh_entry.get().strip()
        gioi_tinh = self.gender_var.get()
        
        # Kiểm tra dữ liệu nhập
        if not ma_nv or not ho_ten:
            messagebox.showerror("Lỗi", "Vui lòng nhập đầy đủ mã nhân viên và họ tên!")
            return
            
        if self.face_image is None:
            messagebox.showerror("Lỗi", "Vui lòng chụp ảnh khuôn mặt trước khi lưu!")
            return
        
        try:
            # Tạo filename cho ảnh khuôn mặt
            face_filename = f"faces/{ma_nv}_{uuid.uuid4().hex}.jpg"
            
            # Lưu ảnh khuôn mặt
            cv2.imwrite(face_filename, self.face_image)
              # Lưu thông tin vào database
            db = sqlite3.connect("employees.db")  # Tạo kết nối mới
            cursor = db.cursor()
            
            # Kiểm tra mã nhân viên đã tồn tại chưa
            cursor.execute("SELECT COUNT(*) FROM nhanvien WHERE ma_nv = ?", (ma_nv,))
            if cursor.fetchone()[0] > 0:
                db.close()
                messagebox.showerror("Lỗi", f"Mã nhân viên {ma_nv} đã tồn tại!")
                return
              # Thêm nhân viên mới
            cursor.execute("""
                INSERT INTO nhanvien (ma_nv, ho_ten, ngay_sinh, gioi_tinh, face_image_path)
                VALUES (?, ?, ?, ?, ?)
            """, (ma_nv, ho_ten, ngay_sinh, gioi_tinh, face_filename))
            
            db.commit()
            db.close()
            messagebox.showinfo("Thành công", f"Đã thêm nhân viên {ho_ten} vào hệ thống!")
            
            # Nếu có callback để refresh danh sách, gọi nó
            if self.refresh_callback:
                self.refresh_callback()
                
            # Đóng window
            self.on_close()
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu thông tin: {str(e)}")
    
    def on_close(self):
        """Xử lý khi đóng cửa sổ"""
        # Dừng camera và giải phóng tài nguyên
        self.is_capturing = False
        
        if hasattr(self, 'cap') and self.cap is not None:
            try:
                self.cap.release()
            except:
                pass
            self.cap = None
        
        try:
            # Đóng tất cả cửa sổ OpenCV
            cv2.destroyAllWindows()
            # Gọi waitKey nhiều lần để đảm bảo OpenCV xử lý các sự kiện
            for i in range(5):
                cv2.waitKey(1)
        except:
            pass
        
        # Đóng cửa sổ Tkinter
        try:
            self.window.destroy()
        except:
            pass

    def evaluate_blur(self, gray_image):
        """Đánh giá độ mờ của ảnh - giá trị cao hơn = ít mờ hơn"""
        return cv2.Laplacian(gray_image, cv2.CV_64F).var()
    
    def evaluate_contrast(self, gray_image):
        """Đánh giá độ tương phản - giá trị cao hơn = tương phản cao hơn"""
        hist = cv2.calcHist([gray_image], [0], None, [256], [0, 256])
        hist_norm = hist.ravel() / hist.sum()
        q_0_1 = np.sum(hist_norm[:26])
        q_0_9 = np.sum(hist_norm[:230])
        if q_0_9 > 0.9 and q_0_1 < 0.1:
            return np.std(gray_image)
        else:
            return 0
    
    def evaluate_brightness(self, gray_image):
        """Đánh giá độ sáng - trả về giá trị trung bình"""
        return np.mean(gray_image)

    def display_quality_feedback(self, frame, message, message_type="error"):
        """Hiển thị thông báo phản hồi trên ảnh"""
        if frame is None:
            return frame
        
        # Tạo bản sao để không ảnh hưởng đến ảnh gốc
        img = frame.copy()
        h, w = img.shape[:2]
        
        # Chọn màu dựa trên loại thông báo
        if message_type == "error":
            color = (0, 0, 255)  # Đỏ cho lỗi
        elif message_type == "warning":
            color = (0, 165, 255)  # Cam cho cảnh báo
        else:
            color = (0, 255, 0)  # Xanh lá cho thành công
        
        # Tạo vùng mờ ở dưới để hiển thị thông báo
        overlay = img.copy()
        cv2.rectangle(overlay, (0, h-60), (w, h), (0, 0, 0), -1)
        alpha = 0.7  # Độ mờ
        cv2.addWeighted(overlay, alpha, img, 1-alpha, 0, img)
        
        # Thêm văn bản
        cv2.putText(img, message, (10, h-25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        return img

    def capture_face(self):
        """Chụp ảnh khuôn mặt nhân viên"""
        # Kiểm tra xem camera có đang chạy không
        if not self.is_capturing or not hasattr(self, 'cap') or self.cap is None or not self.cap.isOpened():
            messagebox.showerror("Lỗi", "Camera không khả dụng. Vui lòng bấm 'Bắt đầu Camera' trước.")
            return
        
        # Thay đổi trạng thái nút để chỉ ra đang xử lý
        try:
            self.capture_button.config(text="Đang xử lý...", state=tk.DISABLED)
            self.window.update()  # Force update UI
        except Exception as e:
            print(f"Lỗi khi cập nhật trạng thái nút: {e}")
        
        # Đảm bảo thư mục faces tồn tại
        self.ensure_faces_directory()
        
        # Đọc khung hình từ camera (đọc nhanh nhiều frame để có được frame mới nhất)
        frame = None
        for _ in range(3):  # Đọc 3 frame để loại bỏ lag
            ret, temp_frame = self.cap.read()
            if ret and temp_frame is not None:
                frame = temp_frame
            time.sleep(0.05)
        
        if frame is None:
            messagebox.showerror("Lỗi", "Không thể đọc dữ liệu từ camera.")
            try:
                self.capture_button.config(text="2. Chụp ảnh", state=tk.NORMAL)
            except:
                pass  # Ignore widget errors
            return
        
        # Đánh giá chất lượng ảnh
        quality_result = self.evaluate_image_quality(frame)
        
        if quality_result != "OK":
            # Hiển thị thông báo lỗi chất lượng ảnh
            self.face_frame = self.display_quality_feedback(frame, quality_result, "error")
            # Cập nhật lại frame để người dùng thấy phản hồi
            try:
                self.update_frame_from_thread(self.face_frame)
            except:
                pass
            self.show_feedback_message(quality_result, "error")
            # Khôi phục trạng thái nút
            try:
                self.capture_button.config(text="2. Chụp ảnh", state=tk.NORMAL)
            except:
                pass  # Ignore widget errors
            return
        
        # Lấy thông tin nhân viên
        ma_nv = self.ma_nv_entry.get().strip()
        ho_ten = self.ho_ten_entry.get().strip()
        
        # Kiểm tra xem đã nhập đủ thông tin chưa
        if not ma_nv or not ho_ten:
            messagebox.showerror("Thiếu thông tin", "Vui lòng nhập đầy đủ mã nhân viên và tên.")
            try:
                self.capture_button.config(text="2. Chụp ảnh", state=tk.NORMAL)
            except:
                pass  # Ignore widget errors
            return
        
        # Tạo tên file ảnh với định dạng: mã_NV_tên_timestamp.jpg
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{ma_nv}_{ho_ten.replace(' ', '_')}_{timestamp}.jpg"
        file_path = os.path.join("faces", filename)
        
        # Lưu ảnh vào thư mục faces
        try:
            cv2.imwrite(file_path, frame)
            print(f"Đã lưu ảnh tại: {file_path}")
            
            # Hiển thị thông báo thành công với màu xanh lá
            success_message = f"✓ Đã chụp ảnh thành công cho {ho_ten}"
            self.show_feedback_message(success_message, "success")
            
            # Cập nhật đường dẫn ảnh vào trường nhập liệu (nếu có)
            if hasattr(self, 'image_path_var'):
                self.image_path_var.set(file_path)
            
            # Hiển thị ảnh đã chụp
            self.face_image = frame.copy()
            
            # Vẽ khung xanh xung quanh khuôn mặt và thêm chữ "ĐÃ CHỤP"
            display_frame = frame.copy()
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
            
            if len(faces) > 0:
                x, y, w, h = faces[0]
                cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                cv2.putText(display_frame, "ĐÃ CHỤP", (x, y-10), 
                          cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
            
            # Cập nhật hiển thị ảnh
            try:
                self.update_frame_from_thread(display_frame)
            except:
                pass
            
            # Cập nhật trạng thái UI
            try:
                self.capture_button.config(text="✓ Đã chụp", bg="#4CAF50", state=tk.DISABLED)
                self.status_var.set(f"✓ Đã chụp ảnh thành công cho {ho_ten}. Bạn có thể nhấn 'Chụp lại' hoặc 'Lưu nhân viên'")
            except Exception as e:
                print(f"Lỗi khi cập nhật UI sau khi chụp: {e}")
        
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu ảnh: {str(e)}")
            print(f"Lỗi khi lưu ảnh: {e}")
            try:
                self.capture_button.config(text="2. Chụp ảnh", state=tk.NORMAL)
            except:
                pass  # Ignore widget errors

    def show_feedback_message(self, message, status="error"):
        """Hiển thị thông báo phản hồi trên giao diện"""
        try:
            feedback_frame = tk.Frame(self.window, bd=2, relief=tk.RAISED)
            feedback_frame.place(relx=0.5, rely=0.92, anchor=tk.CENTER, width=600, height=60)
            
            # Chọn màu sắc dựa trên trạng thái
            if status == "success":
                bg_color = "#e6ffe6"  # Nền xanh nhạt
                fg_color = "#006600"  # Chữ xanh đậm
                feedback_frame.config(bg=bg_color, highlightbackground="#00cc00", highlightthickness=2)
            elif status == "warning":
                bg_color = "#fff9e6"  # Nền vàng nhạt
                fg_color = "#cc7a00"  # Chữ cam
                feedback_frame.config(bg=bg_color, highlightbackground="#ffcc00", highlightthickness=2)
            else:  # error
                bg_color = "#ffe6e6"  # Nền đỏ nhạt
                fg_color = "#cc0000"  # Chữ đỏ đậm
                feedback_frame.config(bg=bg_color, highlightbackground="#ff1a1a", highlightthickness=2)
            
            # Tạo nhãn thông báo
            feedback_label = tk.Label(feedback_frame, text=message, font=("Arial", 12, "bold"),
                                    fg=fg_color, bg=bg_color, wraplength=550, justify="center")
            feedback_label.pack(fill="both", expand=True, padx=10, pady=5)
            
            # Tự động xóa thông báo sau 5 giây
            if hasattr(self, 'feedback_timer'):
                try:
                    self.window.after_cancel(self.feedback_timer)
                except:
                    pass
            
            self.feedback_timer = self.window.after(5000, lambda: feedback_frame.destroy())
            
            # Cập nhật nhãn phản hồi chính nếu tồn tại
            if hasattr(self, 'feedback_label') and self.feedback_label.winfo_exists():
                try:
                    if status == "success":
                        self.feedback_label.config(text=message, fg="green")
                    elif status == "warning":
                        self.feedback_label.config(text=message, fg="orange")
                    else:
                        self.feedback_label.config(text=message, fg="red")
                except:
                    print("Không thể cập nhật nhãn feedback")
        except Exception as e:
            print(f"Lỗi hiển thị thông báo phản hồi: {e}")
            # Fallback to simple message box
            if status == "error":
                messagebox.showerror("Lỗi", message)
            elif status == "warning":
                messagebox.showwarning("Cảnh báo", message)
            else:
                messagebox.showinfo("Thông báo", message)

    def ensure_faces_directory(self):
        """Kiểm tra và tạo thư mục faces nếu chưa tồn tại"""
        if not os.path.exists("faces"):
            os.makedirs("faces")
            print("Đã tạo thư mục faces")

    def update_frame(self, frame=None):
        """Cập nhật khung hình camera trong giao diện"""
        if self.is_capturing and self.cap is not None and self.cap.isOpened():
            # Nếu không có frame cụ thể được cung cấp, đọc từ camera
            if frame is None:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    print("Không thể đọc dữ liệu từ camera.")
                    return
            
            # Xử lý frame cho hiển thị
            try:
                # Chuyển đổi màu từ BGR sang RGB (cho Tkinter)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Phát hiện khuôn mặt để vẽ khung
                # Chỉ sử dụng bản sao của frame để không ảnh hưởng đến frame gốc
                display_frame = rgb_frame.copy()
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(120, 120))
                
                for (x, y, w, h) in faces:
                    # Vẽ khung xanh lá quanh khuôn mặt
                    cv2.rectangle(display_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                    
                    # Hiển thị thông tin hướng dẫn
                    guide_text = "Di chuyển để khuôn mặt nằm trong khung hình"
                    cv2.putText(display_frame, guide_text, (10, 30), 
                               cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                
                # Hiển thị số frame phát hiện liên tục
                detection_text = f"Frames: {self.detection_frames}/30"
                cv2.putText(display_frame, detection_text, (display_frame.shape[1] - 150, 30), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 165, 255), 2)
                
                # Tạo encoding ppm để hiển thị trong Tkinter
                _, enc_img = cv2.imencode('.ppm', display_frame)
                img_bytes = enc_img.tobytes()
                
                # Tạo hình ảnh Tkinter từ frame đã xử lý
                img = tk.PhotoImage(data=img_bytes)
                
                # Hiển thị hình ảnh trong canvas
                self.camera_canvas.img = img
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=img)
                
                # Cập nhật lại sau 30ms
                self.window.after(30, self.update_frame)
            
            except Exception as e:
                print(f"Lỗi khi cập nhật khung hình: {e}")
                self.status_var.set(f"Lỗi cập nhật camera: {str(e)}")
                self.window.after(100, self.update_camera)
        
        # Nếu không phải đang chụp và được cung cấp frame cụ thể (để hiển thị ảnh đã chụp)
        elif frame is not None:
            try:
                # Chuyển đổi màu nếu cần
                if len(frame.shape) == 3:
                    img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                else:
                    img_rgb = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
                
                # Tạo encoding ppm để hiển thị trong Tkinter
                _, enc_img = cv2.imencode('.ppm', img_rgb)
                img_bytes = enc_img.tobytes()
                
                # Tạo hình ảnh Tkinter
                img = tk.PhotoImage(data=img_bytes)
                
                # Hiển thị hình ảnh
                self.camera_canvas.img = img
                self.camera_canvas.create_image(0, 0, anchor=tk.NW, image=img)
            except Exception as e:
                print(f"Lỗi khi hiển thị khung hình cụ thể: {e}")