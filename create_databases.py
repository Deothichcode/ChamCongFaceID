import sqlite3

def create_databases():
    # Tạo database cho nhân viên
    conn = sqlite3.connect('employees.db')
    cursor = conn.cursor()
    
    # Tạo bảng nhanvien với các trường mới
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS nhanvien (
            stt INTEGER PRIMARY KEY,
            ma_nv TEXT UNIQUE,
            ho_ten TEXT,
            ngay_sinh TEXT,
            sdt TEXT,
            que_quan TEXT,
            gioi_tinh TEXT,
            face_encodings TEXT
        )
    ''')
    
    # Tạo bảng cham_cong để lưu thông tin chấm công
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cham_cong (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ma_nv TEXT,
            ho_ten TEXT,
            thoi_gian TEXT,
            FOREIGN KEY (ma_nv) REFERENCES nhanvien(ma_nv)
        )
    ''')
    
    conn.commit()
    conn.close()

    # Tạo database cho admin
    conn = sqlite3.connect('admin.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS admin (
            username TEXT PRIMARY KEY,
            password TEXT
        )
    ''')
    
    # Thêm admin mặc định nếu chưa có
    cursor.execute("INSERT OR IGNORE INTO admin (username, password) VALUES (?, ?)",
                  ('admin', 'admin123'))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    create_databases()

print("Đã tạo 2 file database: admin.db và employees.db")