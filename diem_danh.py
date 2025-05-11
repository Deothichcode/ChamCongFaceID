import tkinter as tk
from tkinter import messagebox
import cv2
import numpy as np
import sqlite3
from datetime import datetime
import threading
import time
from styles import create_label, create_attendance_button
import os
import sys
import io
from PIL import Image, ImageTk

# Fix encoding issues for console output - compatible with all Python versions
try:
    # For Python 3.7+
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    else:
        # For older Python versions
        if sys.platform.startswith('win'):
            # On Windows, redirect stdout/stderr to avoid encoding errors
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace', line_buffering=True)
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace', line_buffering=True)
except Exception as e:
    # If encoding fix fails, just continue with a warning
    print(f"Warning: Could not set console encoding: {e}")

# Disable fancy console printing altogether (alternative approach)
def safe_print(*args, **kwargs):
    try:
        print(*args, **kwargs)
    except UnicodeEncodeError:
        # Try printing with ASCII encoding
        try:
            ascii_args = [str(arg).encode('ascii', 'replace').decode('ascii') for arg in args]
            print(*ascii_args, **kwargs)
        except:
            # Last resort: completely ignore the error
            pass

class DiemDanh:
    def __init__(self, parent, main_app):
        self.parent = parent
        self.main_app = main_app  # Lưu reference đến ứng dụng chính
        self.window = tk.Toplevel(parent)  # Tạo cửa sổ mới
        self.window.title("Điểm danh")
        self.window.geometry("600x500")  # Điều chỉnh kích thước cửa sổ
        
        self.cap = None
        self.is_scanning = False
        self.scan_timer = None
        # Sử dụng bộ phát hiện khuôn mặt của OpenCV
        self.face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        # Lưu trữ các nhân viên đã điểm danh trong phiên quét này
        self.recorded_employees = set()
        # Biến cờ để tránh hiển thị thông báo quá nhiều
        self.show_success_message = True
        # Đảm bảo thư mục faces tồn tại
        self.ensure_faces_directory()
        # Khởi tạo bộ đếm frame để giảm tần suất xử lý
        self.frame_counter = 0
        
        # Thêm biến lưu trữ dữ liệu huấn luyện
        self.face_encodings = {}
        self.face_names = {}
        
        # Huấn luyện dữ liệu khi khởi tạo
        self.train_data()
        
        self.create_widgets()

    def create_widgets(self):
        # Tiêu đề
        title_label = create_label(self.window, "ĐIỂM DANH")
        title_label.pack(pady=20)

        # Frame chứa camera
        self.camera_frame = tk.Frame(self.window)
        self.camera_frame.pack(pady=10)
        
        # Label hiển thị camera
        self.camera_label = tk.Label(self.camera_frame)
        self.camera_label.pack()

        # Frame chứa các nút
        button_frame = tk.Frame(self.window)
        button_frame.pack(pady=20)

        # Nút bắt đầu quét
        self.scan_button = create_attendance_button(button_frame, "Bắt đầu quét", self.toggle_scan)
        self.scan_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Nút lưu điểm danh (ban đầu ẩn)
        self.save_button = create_attendance_button(button_frame, "Lưu điểm danh", self.save_attendance)
        self.save_button.pack(side=tk.LEFT, padx=10, pady=10)
        self.save_button.config(state=tk.DISABLED)  # Ban đầu nút bị vô hiệu hóa

        # Nút quay lại
        back_button = create_attendance_button(button_frame, "Quay lại", self.go_back, bg_color="#F44336")
        back_button.pack(side=tk.LEFT, padx=10, pady=10)

        # Label hiển thị trạng thái
        self.status_label = create_label(self.window, "", font=("Arial", 16))
        self.status_label.pack(pady=20)
        
        # Tạo Text widget để hiển thị thông tin điểm danh
        attendance_frame = tk.Frame(self.window)
        attendance_frame.pack(pady=10, fill=tk.BOTH, expand=True)
        
        attendance_label = create_label(attendance_frame, "Thông tin điểm danh:")
        attendance_label.pack(anchor=tk.W, padx=20, pady=5)
        
        self.attendance_info = tk.Text(attendance_frame, height=6, width=40, font=("Arial", 12))
        self.attendance_info.pack(padx=20, pady=5, fill=tk.BOTH, expand=True)
        self.attendance_info.insert(tk.END, "Chưa có thông tin điểm danh.\nVui lòng bắt đầu quét để điểm danh.")
        
        # Biến lưu trữ thông tin nhân viên đã nhận diện
        self.detected_employee = None
        
        # Xử lý sự kiện đóng cửa sổ
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)

    def go_back(self):
        self.stop_scan()
        self.window.destroy()
        self.main_app.show()  # Hiển thị lại giao diện chính

    def show(self):
        # Đảm bảo cửa sổ được hiển thị
        self.window.deiconify()
        self.window.focus_force()

    def toggle_scan(self):
        if not self.is_scanning:
            self.start_scan()
        else:
            self.stop_scan()

    def ensure_faces_directory(self):
        """Đảm bảo thư mục faces tồn tại để lưu trữ ảnh khuôn mặt"""
        faces_dir = "faces"
        if not os.path.exists(faces_dir):
            safe_print(f"Tạo thư mục {faces_dir}")
            os.makedirs(faces_dir)

    def start_scan(self):
        try:
            print("Starting scan...")
            # Ensure camera is released if it was previously opened
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                cv2.destroyAllWindows()
                time.sleep(1)  # Wait for camera to fully release

            # Try to open camera with different backends
            for backend in [cv2.CAP_DSHOW, cv2.CAP_MSMF, cv2.CAP_ANY]:
                self.cap = cv2.VideoCapture(0, backend)
                if self.cap.isOpened():
                    print(f"Camera opened successfully with backend: {backend}")
                    break
                else:
                    print(f"Failed to open camera with backend: {backend}")
                    if self.cap is not None:
                        self.cap.release()
                        self.cap = None

            if self.cap is None or not self.cap.isOpened():
                raise Exception("Không thể mở camera. Vui lòng kiểm tra kết nối camera.")

            # Set camera properties
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)

            # Test camera read
            ret, frame = self.cap.read()
            if not ret:
                raise Exception("Không thể đọc dữ liệu từ camera")

            self.is_scanning = True
            self.scan_button.config(text="Dừng quét")
            self.status_label.config(text="Đang quét...")
            self.update_frame()
        except Exception as e:
            print(f"Error in start_scan: {str(e)}")
            if self.cap is not None:
                self.cap.release()
                self.cap = None
            self.is_scanning = False
            self.scan_button.config(text="Bắt đầu quét")
            self.status_label.config(text="Lỗi: " + str(e))
            messagebox.showerror("Lỗi", str(e))

    def stop_scan_from_timer(self):
        """Gọi stop_scan từ thread timer bằng cách đưa vào thread chính"""
        self.window.after(0, self.stop_scan)

    def stop_scan(self):
        """Dừng quét khuôn mặt và giải phóng tài nguyên"""
        safe_print("Dừng quét và giải phóng tài nguyên")
        
        # Đánh dấu dừng quét
        self.is_scanning = False
        
        # Hủy timer nếu đang chạy
        if self.scan_timer:
            self.scan_timer.cancel()
            self.scan_timer = None
            
        # Cập nhật UI
        self.scan_button.config(text="Bắt đầu quét")
        self.status_label.config(text="Quét hoàn tất")
        self.save_button.config(state=tk.DISABLED)  # Vô hiệu hóa nút lưu
        
        # Giải phóng camera
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception as e:
                safe_print(f"Lỗi giải phóng camera: {str(e)}")
            finally:
                self.cap = None
        
        # Xóa hình ảnh camera
        self.camera_label.configure(image='')
        self.camera_label.image = None

    def update_frame(self):
        if not self.is_scanning or self.cap is None:
            return

        try:
            # Read frame from camera
            ret, frame = self.cap.read()
            if not ret or frame is None:
                print("Failed to read frame from camera")
                self.stop_scan()
                return

            # Flip frame horizontally for correct display
            frame = cv2.flip(frame, 1)

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive histogram equalization to improve contrast
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            gray = clahe.apply(gray)
            
            # Apply Gaussian blur to reduce noise
            gray = cv2.GaussianBlur(gray, (3, 3), 0)

            # Detect faces with adjusted parameters
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(100, 100),
                maxSize=(300, 300)
            )

            # Draw rectangles around faces and process recognition
            for (x, y, w, h) in faces:
                # Draw rectangle around face
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
                # Extract face region for recognition
                face_roi = frame[y:y+h, x:x+w]
                
                # Try to identify the employee
                employee = self.identify_employee(face_roi)
                
                if employee:
                    # Lưu thông tin nhân viên đã nhận diện
                    self.detected_employee = employee
                    # Kích hoạt nút lưu điểm danh
                    self.save_button.config(state=tk.NORMAL)
                    # Hiển thị thông tin nhân viên
                    self.status_label.config(text=f"Đã nhận diện: {employee['ho_ten']}")
                    # Hiển thị thông tin trong attendance_info
                    self.attendance_info.delete(1.0, tk.END)
                    self.attendance_info.insert(tk.END, f"Mã NV: {employee['ma_nv']}\n")
                    self.attendance_info.insert(tk.END, f"Họ tên: {employee['ho_ten']}\n")
                    self.attendance_info.insert(tk.END, "Vui lòng bấm nút 'Lưu điểm danh' để xác nhận")
                else:
                    # Không nhận diện được, giữ trạng thái mặc định
                    self.detected_employee = None
                    self.save_button.config(state=tk.DISABLED)
                    self.status_label.config(text="Đang quét...")
                    self.attendance_info.delete(1.0, tk.END)
                    self.attendance_info.insert(tk.END, "Vui lòng kiểm tra khuôn mặt hoặc đăng ký nhân viên mới.\n")

            # Convert frame to RGB for display in tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frame_rgb = cv2.resize(frame_rgb, (640, 480))
            
            # Convert to PhotoImage
            photo = ImageTk.PhotoImage(image=Image.fromarray(frame_rgb))
            
            # Update camera label
            self.camera_label.configure(image=photo)
            self.camera_label.image = photo  # Keep a reference

            # Schedule next frame update
            if self.is_scanning:
                self.window.after(30, self.update_frame)

        except Exception as e:
            print(f"Error in update_frame: {str(e)}")
            self.stop_scan()
            messagebox.showerror("Lỗi", f"Lỗi khi xử lý camera: {str(e)}")

    def train_data(self):
        """Huấn luyện dữ liệu khuôn mặt từ database"""
        try:
            # Kết nối database
            conn = sqlite3.connect('employees.db')
            cursor = conn.cursor()
            
            # Lấy danh sách nhân viên có ảnh khuôn mặt
            cursor.execute("SELECT ma_nv, ho_ten, face_image_path FROM nhanvien WHERE face_image_path IS NOT NULL")
            employees = cursor.fetchall()
            
            if not employees:
                print("Không có dữ liệu khuôn mặt để huấn luyện")
                return
                
            print(f"Bắt đầu huấn luyện dữ liệu cho {len(employees)} nhân viên...")
            
            for ma_nv, ho_ten, face_path in employees:
                try:
                    # Đọc ảnh khuôn mặt
                    face_image = cv2.imread(face_path)
                    if face_image is None:
                        print(f"Không thể đọc ảnh của nhân viên {ma_nv}")
                        continue
                        
                    # Chuyển sang ảnh xám
                    gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
                    
                    # Áp dụng CLAHE để cân bằng ánh sáng
                    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                    gray = clahe.apply(gray)
                    
                    # Làm mờ để giảm nhiễu
                    gray = cv2.GaussianBlur(gray, (3, 3), 0)
                    
                    # Phát hiện khuôn mặt
                    faces = self.face_cascade.detectMultiScale(
                        gray,
                        scaleFactor=1.1,
                        minNeighbors=5,
                        minSize=(100, 100)
                    )
                    
                    if len(faces) == 0:
                        print(f"Không phát hiện được khuôn mặt trong ảnh của nhân viên {ma_nv}")
                        continue
                        
                    # Lấy khuôn mặt đầu tiên
                    x, y, w, h = faces[0]
                    face_roi = gray[y:y+h, x:x+w]
                    
                    # Resize về kích thước chuẩn
                    face_roi = cv2.resize(face_roi, (150, 150))
                    
                    # Lưu đặc trưng khuôn mặt
                    self.face_encodings[ma_nv] = face_roi
                    self.face_names[ma_nv] = ho_ten
                    
                    print(f"Đã huấn luyện xong cho nhân viên {ma_nv} - {ho_ten}")
                    
                except Exception as e:
                    print(f"Lỗi khi huấn luyện cho nhân viên {ma_nv}: {str(e)}")
                    continue
                    
            print("Hoàn thành huấn luyện dữ liệu")
            
        except Exception as e:
            print(f"Lỗi trong quá trình huấn luyện: {str(e)}")
        finally:
            if 'conn' in locals():
                conn.close()

    def identify_employee(self, face_image):
        try:
            # Check if face image is valid
            if face_image is None or face_image.size == 0:
                print("Invalid face image")
                return None

            # Convert to grayscale
            face_gray = cv2.cvtColor(face_image, cv2.COLOR_BGR2GRAY)
            
            # Apply adaptive histogram equalization for better lighting handling
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
            face_gray = clahe.apply(face_gray)
            
            # Apply Gaussian blur to reduce noise
            face_gray = cv2.GaussianBlur(face_gray, (3, 3), 0)
            
            # Resize face image to match training size
            face_gray = cv2.resize(face_gray, (150, 150))
            
            # Initialize variables for best match
            best_match = None
            min_diff = float('inf')
            
            # Kiểm tra xem có dữ liệu khuôn mặt nào trong cơ sở dữ liệu không
            if not self.face_encodings:
                print("Không có dữ liệu khuôn mặt trong cơ sở dữ liệu")
                return None
            
            # So sánh với tất cả các khuôn mặt đã huấn luyện
            for ma_nv, stored_face in self.face_encodings.items():
                try:
                    # Phương pháp 1: L2 norm (khoảng cách Euclid)
                    diff = cv2.norm(face_gray, stored_face, cv2.NORM_L2)
                    diff = diff / (face_gray.shape[0] * face_gray.shape[1])  # Chuẩn hóa theo kích thước ảnh
                    
                    # Phương pháp 2: Template matching
                    result = cv2.matchTemplate(face_gray, stored_face, cv2.TM_CCOEFF_NORMED)
                    template_diff = 1 - result[0][0]
                    
                    # Phương pháp 3: Histogram comparison
                    hist1 = cv2.calcHist([face_gray], [0], None, [256], [0, 256])
                    hist2 = cv2.calcHist([stored_face], [0], None, [256], [0, 256])
                    hist_diff = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
                    hist_diff = 1 - hist_diff
                    
                    # Kết hợp các phương pháp với trọng số
                    combined_diff = (diff * 0.3) + (template_diff * 0.4) + (hist_diff * 0.3)
                    
                    print(f"So sánh với {self.face_names[ma_nv]} (ID: {ma_nv}):")
                    print(f"- L2 norm: {diff:.4f}")
                    print(f"- Template matching: {template_diff:.4f}")
                    print(f"- Histogram: {hist_diff:.4f}")
                    print(f"- Tổng hợp: {combined_diff:.4f}")
                    
                    # Cập nhật kết quả tốt nhất nếu tìm thấy kết quả tốt hơn
                    if combined_diff < min_diff:
                        min_diff = combined_diff
                        best_match = {
                            'ma_nv': ma_nv,
                            'ho_ten': self.face_names[ma_nv],
                            'diff': combined_diff
                        }
                except Exception as e:
                    print(f"Lỗi khi so sánh với nhân viên {ma_nv}: {str(e)}")
                    continue
            
            # Nếu tìm thấy kết quả tốt nhất và độ khác biệt nhỏ hơn ngưỡng
            if best_match and best_match['diff'] < 0.85:  # Ngưỡng 0.85 để tăng độ chính xác
                print(f"Nhận diện thành công: {best_match['ho_ten']} (ID: {best_match['ma_nv']})")
                print(f"Độ khác biệt: {best_match['diff']:.4f}")
                return best_match
            else:
                # Không nhận diện được, trả về None
                print("Không tìm thấy kết quả phù hợp hoặc độ khác biệt quá cao.")
                if best_match:
                    print(f"Kết quả tốt nhất: {best_match['ho_ten']} với độ khác biệt: {min_diff:.4f}")
                return None
            
        except Exception as e:
            print(f"Lỗi trong quá trình nhận diện: {str(e)}")
            return None

    def record_attendance(self, ma_nv, ho_ten):
        safe_print(f"Ghi nhận điểm danh cho nhân viên: {ma_nv}")
        conn = None
        try:
            conn = sqlite3.connect('employees.db')
            cursor = conn.cursor()
            
            # Đảm bảo bảng cham_cong đã được tạo
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS cham_cong (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    ma_nv TEXT,
                    ho_ten TEXT,
                    thoi_gian TEXT
                )
            ''')
            
            # Kiểm tra xem nhân viên đã điểm danh hôm nay chưa
            today = datetime.now().strftime('%Y-%m-%d')
            cursor.execute('''
                SELECT COUNT(*) FROM cham_cong 
                WHERE ma_nv = ? AND date(thoi_gian) = ?
            ''', (ma_nv, today))
            
            count = cursor.fetchone()[0]
            current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            if count > 0:
                # Đã điểm danh rồi
                safe_print(f"Nhân viên {ma_nv} đã điểm danh ngày hôm nay rồi.")
                messagebox.showinfo("Thông báo", 
                                   f"Nhân viên {ho_ten} đã điểm danh hôm nay rồi.\n"
                                   f"Thời gian: {current_time}")
                # Quay lại trang chủ sau 1 giây
                self.window.after(1000, self.go_back)
            else:
                # Chưa điểm danh, thêm vào bảng cham_cong
                cursor.execute('''
                    INSERT INTO cham_cong (ma_nv, ho_ten, thoi_gian)
                    VALUES (?, ?, ?)
                ''', (ma_nv, ho_ten, current_time))
                
                conn.commit()
                
                safe_print(f"Đã điểm danh thành công cho {ma_nv} vào lúc {current_time}")
                messagebox.showinfo("Điểm danh thành công", 
                                   f"Đã điểm danh thành công cho nhân viên:\n"
                                   f"Mã NV: {ma_nv}\n"
                                   f"Họ tên: {ho_ten}\n"
                                   f"Thời gian: {current_time}")
                
                # Cập nhật trạng thái trên giao diện
                self.status_label.config(text=f"Đã điểm danh: {ho_ten} ({current_time})")
                
                # Hiển thị thông tin điểm danh trên giao diện
                self.attendance_info.delete(1.0, tk.END)
                self.attendance_info.insert(tk.END, f"Mã nhân viên: {ma_nv}\n")
                self.attendance_info.insert(tk.END, f"Họ và tên: {ho_ten}\n")
                self.attendance_info.insert(tk.END, f"Thời gian: {current_time}\n")
                self.attendance_info.insert(tk.END, f"Trạng thái: Điểm danh thành công")
                
                # Quay lại trang chủ sau 2 giây
                self.window.after(2000, self.go_back)
                
        except Exception as e:
            safe_print(f"Lỗi ghi nhận điểm danh: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể ghi nhận điểm danh: {str(e)}")
            if conn:
                conn.rollback()
        finally:
            if conn:
                conn.close()
                safe_print("Đã đóng kết nối database sau khi điểm danh")

    def on_close(self):
        """Xử lý khi đóng cửa sổ"""
        self.stop_scan()
        self.window.destroy()
        self.main_app.show()

    def test_camera(self):
        """Kiểm tra camera có hoạt động không"""
        self.status_label.config(text="Đang kiểm tra camera...")
        
        try:
            # Đảm bảo camera đã đóng
            if self.cap is not None:
                self.cap.release()
                self.cap = None
                time.sleep(0.5)
                
            # Thử các phương pháp mở camera
            cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not cap.isOpened():
                cap.release()
                cap = cv2.VideoCapture(0)
                if not cap.isOpened():
                    self.status_label.config(text="Không thể mở camera!")
                    messagebox.showerror("Lỗi", "Không thể mở camera! Vui lòng kiểm tra kết nối.")
                    return
                
            # Thiết lập độ phân giải
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                
            # Đọc 5 frame đầu tiên để đảm bảo camera đã hoạt động
            for i in range(5):
                ret, frame = cap.read()
                if not ret:
                    break
                time.sleep(0.1)
                
            # Đọc frame cuối cùng để hiển thị
            ret, frame = cap.read()
            if not ret:
                self.status_label.config(text="Không thể đọc dữ liệu từ camera!")
                messagebox.showerror("Lỗi", "Không thể đọc dữ liệu từ camera!")
                cap.release()
                return
                
            # Hiển thị thông báo và frame
            self.status_label.config(text="Camera hoạt động bình thường!")
            messagebox.showinfo("Thành công", "Camera hoạt động bình thường!")
            
            # Hiển thị frame
            cv2.namedWindow('Test Camera', cv2.WINDOW_NORMAL)
            cv2.imshow('Test Camera', frame)
            cv2.waitKey(3000)  # Hiển thị 3 giây
            
            # Đóng camera
            cap.release()
            cv2.destroyAllWindows()
            for i in range(5):
                cv2.waitKey(1)
            
        except Exception as e:
            safe_print(f"Lỗi kiểm tra camera: {str(e)}")
            self.status_label.config(text=f"Lỗi: {str(e)}")
            messagebox.showerror("Lỗi", f"Không thể kiểm tra camera: {str(e)}")

    def save_attendance(self):
        if self.detected_employee is None:
            messagebox.showerror("Lỗi", "Không có thông tin nhân viên để lưu!")
            return
            
        try:
            # Ghi nhận điểm danh
            self.record_attendance(self.detected_employee['ma_nv'], self.detected_employee['ho_ten'])
            # Dừng quét
            self.stop_scan()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể lưu điểm danh: {str(e)}")