import os
import sqlite3

DB_PATH = os.path.join(os.path.dirname(__file__), "itm_university.db")

def init_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.executescript("""
    PRAGMA foreign_keys = ON;

    CREATE TABLE departments (
        dept_code TEXT PRIMARY KEY,
        dept_name TEXT NOT NULL,
        hod_name TEXT NOT NULL,
        location TEXT NOT NULL
    );

    INSERT INTO departments VALUES
    ('CSE', 'Computer Science & Engineering', 'Dr. Alok Verma', 'Tech Block A, 3rd Floor'),
    ('AI & DS', 'Artificial Intelligence & Data Science', 'Dr. Sunita Deshmukh', 'Innovation Lab, 2nd Floor'),
    ('Cyber Sec', 'Cyber Security & Forensics', 'Dr. Rajesh Mehta', 'Cyber Shield Wing, 1st Floor'),
    ('Cloud Comp', 'Cloud Computing & DevOps', 'Prof. Arvind Rao', 'Tech Block B, 4th Floor');

    CREATE TABLE faculty (
        faculty_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        dept_code TEXT NOT NULL,
        designation TEXT NOT NULL,
        experience_years INTEGER NOT NULL,
        FOREIGN KEY(dept_code) REFERENCES departments(dept_code)
    );

    INSERT INTO faculty VALUES
    ('FAC01', 'Dr. Sunita Deshmukh', 'AI & DS', 'Professor & HOD', 16),
    ('FAC02', 'Prof. Sameer Kulkarni', 'AI & DS', 'Associate Professor', 9),
    ('FAC03', 'Dr. Rajesh Mehta', 'Cyber Sec', 'Professor & HOD', 14),
    ('FAC04', 'Prof. Neha Kapoor', 'CSE', 'Assistant Professor', 6),
    ('FAC05', 'Prof. Arvind Rao', 'Cloud Comp', 'Associate Professor', 11),
    ('FAC06', 'Dr. Alok Verma', 'CSE', 'Professor & HOD', 18);

    CREATE TABLE courses (
        course_id TEXT PRIMARY KEY,
        course_name TEXT NOT NULL,
        branch TEXT NOT NULL,
        semester INTEGER NOT NULL,
        credits INTEGER NOT NULL,
        faculty_id TEXT NOT NULL,
        FOREIGN KEY(branch) REFERENCES departments(dept_code),
        FOREIGN KEY(faculty_id) REFERENCES faculty(faculty_id)
    );

    INSERT INTO courses VALUES
    ('CS401', 'Large Language Models & GenAI', 'AI & DS', 7, 4, 'FAC01'),
    ('CS402', 'Deep Learning & Neural Networks', 'AI & DS', 6, 4, 'FAC02'),
    ('CS301', 'Data Structures & Algorithms', 'CSE', 3, 4, 'FAC04'),
    ('CS302', 'Database Management Systems', 'CSE', 4, 3, 'FAC06'),
    ('SEC401', 'Ethical Hacking & Penetration Testing', 'Cyber Sec', 7, 4, 'FAC03'),
    ('SEC302', 'Cryptography & Network Security', 'Cyber Sec', 5, 3, 'FAC03'),
    ('CLD301', 'Kubernetes & Cloud Native Architectures', 'Cloud Comp', 6, 3, 'FAC05'),
    ('CLD201', 'Linux Systems & Shell Automation', 'Cloud Comp', 3, 2, 'FAC05');

    CREATE TABLE students (
        student_id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        branch TEXT NOT NULL,
        semester INTEGER NOT NULL,
        cgpa REAL NOT NULL,
        attendance_pct INTEGER NOT NULL,
        fees_status TEXT NOT NULL CHECK(fees_status IN ('Paid', 'Pending', 'Partial')),
        FOREIGN KEY(branch) REFERENCES departments(dept_code)
    );

    INSERT INTO students VALUES
    ('ITM101', 'Aarav Sharma', 'CSE', 7, 8.9, 84, 'Paid'),
    ('ITM102', 'Priya Patel', 'CSE', 7, 9.4, 92, 'Paid'),
    ('ITM103', 'Rohan Verma', 'Cyber Sec', 5, 7.8, 68, 'Pending'),
    ('ITM104', 'Ananya Iyer', 'AI & DS', 7, 9.7, 96, 'Paid'),
    ('ITM105', 'Vikram Singh', 'CSE', 5, 8.2, 71, 'Paid'),
    ('ITM106', 'Sneha Kulkarni', 'Cyber Sec', 3, 8.7, 89, 'Paid'),
    ('ITM107', 'Rahul Nair', 'CSE', 7, 9.1, 74, 'Paid'),
    ('ITM108', 'Kavita Joshi', 'AI & DS', 5, 8.6, 81, 'Pending'),
    ('ITM109', 'Aditya Sen', 'Cloud Comp', 6, 8.4, 73, 'Paid'),
    ('ITM110', 'Ishita Mehra', 'AI & DS', 7, 9.3, 90, 'Paid'),
    ('ITM111', 'Manish Pandey', 'Cyber Sec', 7, 7.5, 64, 'Pending'),
    ('ITM112', 'Pooja Chawla', 'Cloud Comp', 4, 8.9, 88, 'Paid'),
    ('ITM113', 'Devendra Reddy', 'CSE', 6, 7.9, 78, 'Paid'),
    ('ITM114', 'Simran Kaur', 'AI & DS', 6, 9.0, 85, 'Paid'),
    ('ITM115', 'Tanmay Bhattacharya', 'Cyber Sec', 5, 8.1, 79, 'Paid');

    CREATE TABLE placements (
        placement_id INTEGER PRIMARY KEY AUTOINCREMENT,
        student_id TEXT NOT NULL,
        company TEXT NOT NULL,
        role TEXT NOT NULL,
        package_lpa REAL NOT NULL,
        placement_type TEXT NOT NULL CHECK(placement_type IN ('Full-Time', 'Internship + PPO')),
        FOREIGN KEY(student_id) REFERENCES students(student_id)
    );

    INSERT INTO placements VALUES
    (1, 'ITM104', 'NVIDIA', 'LLM Alignment Engineer', 34.0, 'Full-Time'),
    (2, 'ITM102', 'Microsoft', 'Data & Applied Scientist', 28.5, 'Full-Time'),
    (3, 'ITM110', 'Google', 'AI Research Engineer', 32.0, 'Full-Time'),
    (4, 'ITM101', 'Amazon AWS', 'Cloud Solutions Architect', 24.0, 'Full-Time'),
    (5, 'ITM107', 'Oracle', 'Systems Performance Engineer', 21.0, 'Full-Time'),
    (6, 'ITM114', 'Adobe', 'Computer Vision Intern', 18.5, 'Internship + PPO'),
    (7, 'ITM105', 'Cisco', 'Network Security Analyst', 16.0, 'Full-Time'),
    (8, 'ITM109', 'Red Hat', 'DevOps & SRE Specialist', 17.5, 'Full-Time');
    """)

    conn.commit()
    conn.close()
    print("Database itm_university.db seeded successfully with 5 tables!")

if __name__ == "__main__":
    init_database()
