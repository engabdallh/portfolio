import sqlite3
import customtkinter as ctk
import tkinter.messagebox as messagebox

# إنشاء قاعدة البيانات وفتح الاتصال
conn = sqlite3.connect("attendance.db")
cursor = conn.cursor()

# إنشاء الجداول إذا لم تكن موجودة
cursor.execute("""
CREATE TABLE IF NOT EXISTS persons (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    national_id TEXT NOT NULL,
    role TEXT NOT NULL,
    course TEXT,
    department TEXT,
    sec TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    person_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    present BOOLEAN NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons (id)
)
""")



cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    course_name TEXT PRIMARY KEY,
    is_open BOOLEAN NOT NULL
)
""")


conn.commit()

# الكلاس الأساسي Person
class Person:
    def __init__(self, name, national_id, role, course=None, department=None, sec=None):
        self.name = name
        self.national_id = national_id
        self.role = role
        self.course = course
        self.department = department
        self.sec = sec
        self.id = None

    def save_to_db(self):
        """حفظ الشخص في قاعدة البيانات"""
        cursor.execute("""
        INSERT INTO persons (name, national_id, role, course, department, sec)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (self.name, self.national_id, self.role, self.course, self.department, self.sec))
        conn.commit()
        self.id = cursor.lastrowid

    def delete_from_db(self):
        """حذف الشخص من قاعدة البيانات"""
        if self.role != "Teacher":
            raise Exception("Only teachers can delete a person.")
        if self.id is None:
            raise Exception("Person must exist in the database first!")
        cursor.execute("DELETE FROM persons WHERE id = ?", (self.id,))
        conn.commit()

    def update_in_db(self, new_course=None, new_department=None, new_sec=None):
        """تحديث بيانات الطالب"""
        if self.role != "Student":
            raise Exception("Only students can update their data.")
        if self.id is None:
            raise Exception("Person must exist in the database first!")
        cursor.execute("""
        UPDATE persons SET course = ?, department = ?, sec = ?
        WHERE id = ?
        """, (new_course, new_department, new_sec, self.id))
        conn.commit()

    def check_absence_warning_gui(self, max_absences=10):
        """التحقق من تجاوز الحد الأقصى للغياب مع عرض إنذار في GUI"""
        if self.id is None:
            raise Exception("Person must exist in the database first!")
        cursor.execute("""
        SELECT COUNT(*) FROM attendance
        WHERE person_id = ? AND present = 0
        """, (self.id,))
        absences = cursor.fetchone()[0]
        if absences > max_absences:
            messagebox.showwarning("Warning", f"{self.name} has exceeded the allowed absences ({absences}/{max_absences}).")
        else:
            messagebox.showinfo("Status", f"{self.name} is within the allowed absence limit ({absences}/{max_absences}).")

    def open_course(self, course_name):
        """فتح كورس معين"""
        if self.role != "Teacher":
            raise PermissionError("Only teachers can open courses.")
        cursor.execute("""
        INSERT INTO courses (course_name, is_open)
        VALUES (?, 1)
        ON CONFLICT(course_name) DO UPDATE SET is_open = 1
        """, (course_name,))
        conn.commit()

    def close_course(self, course_name):
        """إغلاق كورس معين"""
        if self.role != "Teacher":
            raise PermissionError("Only teachers can close courses.")
        cursor.execute("""
        UPDATE courses SET is_open = 0 WHERE course_name = ?
        """, (course_name,))
        conn.commit()



PASSWORDS = {
    "Teacher": "teacher123",  # كلمة مرور المدرس
    "Admin": "admin123",    # كلمة مرور العامل
}

def require_password(role, on_success):
    """عرض نافذة إدخال كلمة المرور للتحقق قبل فتح الشاشة."""
    def verify_password():
        entered_password = password_entry.get()
        if PASSWORDS.get(role) == entered_password:
            password_window.destroy()
            on_success()
        else:
            messagebox.showerror("Error", "Incorrect password!")

    # إنشاء نافذة إدخال كلمة المرور
    password_window = ctk.CTkToplevel()
    password_window.title(f"{role} Authentication")
    password_window.geometry("300x200")

    label = ctk.CTkLabel(password_window, text=f"Enter {role} Password:", font=("Arial", 14))
    label.pack(pady=20)

    password_entry = ctk.CTkEntry(password_window, show="*", font=("Arial", 14))
    password_entry.pack(pady=10)

    button_submit = ctk.CTkButton(password_window, text="Submit", command=verify_password)
    button_submit.pack(pady=10)

    password_window.transient(app.root)  # التأكد من أن النافذة تظهر فوق الرئيسية
    password_window.grab_set()          # منع التفاعل مع النافذة الرئيسية
    password_window.mainloop()


# واجهة المستخدم
class App:
    def __init__(self, root):
        self.root = root
        self.main_menu()

    def main_menu(self):
        for widget in self.root.winfo_children():
            widget.destroy()

        label_title = ctk.CTkLabel(self.root, text="Select Category", font=("Arial", 30, "bold"))
        label_title.pack(pady=50)

        button_student = ctk.CTkButton(self.root, text="Student", command=self.student_menu, width=200, height=50, font=("Arial", 16))
        button_student.pack(pady=15)

        # button_teacher = ctk.CTkButton(self.root, text="Teacher", command=self.teacher_menu, width=200, height=50, font=("Arial", 16))
        # button_teacher.pack(pady=15)

        # button_admin = ctk.CTkButton(self.root, text="Admin", command=self.admin_menu, width=200, height=50, font=("Arial", 16))
        # button_admin.pack(pady=15)


        button_teacher = ctk.CTkButton(
            self.root, 
            text="Teacher", 
            command=lambda: require_password("Teacher", self.teacher_menu), 
            width=200, 
            height=50, 
            font=("Arial", 18)
        )
        button_teacher.pack(pady=15)

        button_admin = ctk.CTkButton(
            self.root, 
            text="Admin", 
            command=lambda: require_password("Admin", self.admin_menu), 
            width=200, 
            height=50, 
            font=("Arial", 18)
        )
        button_admin.pack(pady=15)

        button_show_records = ctk.CTkButton(self.root, text="Show All Records", command=self.show_all_records, width=200, height=50, font=("Arial", 16))
        button_show_records.pack(pady=15)

    def setup_input_screen(self, role, course_options=None,department_options=None, sec_options=None):
        for widget in self.root.winfo_children():
            widget.destroy()

        label_title = ctk.CTkLabel(self.root, text=f"{role} Registration", font=("Arial", 25, "bold"))
        label_title.pack(pady=20)

        self.create_label("Name:")
        self.entry_name = self.create_entry()

        self.create_label("National ID:")
        self.entry_national_id = self.create_entry()



        # عرض الحقل الخاص بـ Course فقط إذا كانت الخيارات موجودة
        if course_options:
            self.create_label("Course:")
            self.entry_course = ctk.CTkComboBox(self.root, values=course_options, font=("Arial", 16))
            self.entry_course.pack(pady=5)

    # عرض الحقل الخاص بـ Department فقط إذا كانت الخيارات موجودة
        if department_options:
            self.create_label("Level:")
            self.entry_department = ctk.CTkComboBox(self.root, values=department_options, font=("Arial", 16))
            self.entry_department.pack(pady=5)

    # عرض الحقل الخاص بـ Sec فقط إذا كانت الخيارات موجودة
        if sec_options:
            self.create_label("Sec:")
            self.entry_sec = ctk.CTkComboBox(self.root, values=sec_options, font=("Arial", 16))
            self.entry_sec.pack(pady=5)

        # self.create_label("Course :")
        # self.entry_course = ctk.CTkComboBox(self.root, values=course_options, font=("Arial", 16))
        # self.entry_course.pack(pady=5)

        # self.create_label("Department:")
        # self.entry_department = ctk.CTkComboBox(self.root, values=department_options, font=("Arial", 16))
        # self.entry_department.pack(pady=5)

        # self.create_label("Sec:")
        # self.entry_sec = ctk.CTkComboBox(self.root, values=sec_options, font=("Arial", 16))
        # self.entry_sec.pack(pady=5)

        button_register = ctk.CTkButton(self.root, text="Register", command=lambda: self.register(role), font=("Arial", 16), width=200, height=50)
        button_register.pack(pady=10)

        button_check_absences = ctk.CTkButton(self.root, text="Check Absences", command=self.check_absences, font=("Arial", 16), width=200, height=50)
        button_check_absences.pack(pady=10)

        # زر الحذف يظهر فقط للمعلم
        if role == "Teacher":
            button_delete = ctk.CTkButton(self.root, text="Delete Person", command=self.delete_person, font=("Arial", 16), width=200, height=50)
            button_delete.pack(pady=10)

        if role == "Teacher":
            button_open = ctk.CTkButton(self.root, text="Open Course", command=self.open_course, font=("Arial", 16), width=200, height=50)
            button_open.pack(pady=10)

        if role == "Teacher":
            button_close = ctk.CTkButton(self.root, text="Close Course", command=self.close_course, font=("Arial", 16), width=200, height=50)
            button_close.pack(pady=10)

        # زر التحديث يظهر فقط للطالب
        if role == "Student":
            button_update = ctk.CTkButton(self.root, text="Update Info", command=self.update_person, font=("Arial", 16), width=200, height=50)
            button_update.pack(pady=10)

        button_back = ctk.CTkButton(self.root, text="Back", command=self.main_menu, font=("Arial", 16), width=200, height=50)
        button_back.pack(pady=5)

    def create_label(self, text):
        label = ctk.CTkLabel(self.root, text=text, font=("Arial", 16))
        label.pack(pady=5)

    def create_entry(self):
        entry = ctk.CTkEntry(self.root, font=("Arial", 16))
        entry.pack(pady=5)
        return entry

    # def register(self, role):
    #     name = self.entry_name.get()
    #     national_id = self.entry_national_id.get()
    #     course = self.entry_course.get()
    #     department = self.entry_department.get()
    #     sec = self.entry_sec.get()

    #     if not name or not national_id:
    #         messagebox.showerror("Error", "Please fill in the required fields: Name and National ID.")
    #         return

    #     person = Person(name, national_id, role, course, department, sec)
    #     person.save_to_db()
    #     messagebox.showinfo("Success", "Person registered successfully!")
    #     self.clear_fields()


    def register(self, role):
        name = self.entry_name.get()
        national_id = self.entry_national_id.get()
        course = self.entry_course.get()
        department = self.entry_department.get()
        sec = self.entry_sec.get()

        if not name or not national_id or not course:
            messagebox.showerror("Error", "Please fill in the required fields: Name, National ID, and Course.")
            return

    # التحقق من حالة المادة
        cursor.execute("SELECT is_open FROM courses WHERE course_name = ?", (course,))
        result = cursor.fetchone()

        if not result:
            messagebox.showerror("Error", f"The course '{course}' does not exist.")
            return

        is_open = result[0]
        if not is_open:
            messagebox.showerror("Error", f"The course '{course}' is currently closed. Please contact your teacher.")
            return

    # التسجيل إذا كانت المادة مفتوحة
        person = Person(name, national_id, role, course, department, sec)
        person.save_to_db()
        messagebox.showinfo("Success", f"{role} '{name}' registered successfully for the course '{course}'!")
        self.clear_fields()

    def delete_person(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showerror("Error", "Please enter a name to delete.")
            return

        cursor.execute("SELECT id FROM persons WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            person_id = result[0]
            person = Person(name, None, None)
            person.id = person_id
            person.delete_from_db()
            messagebox.showinfo("Success", f"Person {name} deleted successfully!")
        else:
            messagebox.showerror("Error", "Person not found in the database.")

    def update_person(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showerror("Error", "Please enter a name to update.")
            return

        cursor.execute("SELECT id, national_id, role FROM persons WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            person_id, national_id, role = result
            new_course = self.entry_course.get()
            new_department = self.entry_department.get()
            new_sec = self.entry_sec.get()

            person = Person(name, national_id, role, new_course, new_department, new_sec)
            person.id = person_id
            person.update_in_db(new_course, new_department, new_sec)
            messagebox.showinfo("Success", f"Information for {name} updated successfully!")
        else:
            messagebox.showerror("Error", "Person not found in the database.")

    def clear_fields(self):
        self.entry_name.delete(0, ctk.END)
        self.entry_national_id.delete(0, ctk.END)
        self.entry_course.delete(0, ctk.END)
        self.entry_department.set("")
        self.entry_sec.set("")

    def show_all_records(self):
        cursor.execute("SELECT * FROM persons")
        records = cursor.fetchall()

        result_window = ctk.CTkToplevel(self.root)
        result_window.title("All Records")
        result_window.geometry("600x400")

        if not records:
            label = ctk.CTkLabel(result_window, text="No records found.", font=("Arial", 16))
            label.pack(pady=20)
        else:
            for record in records:
                person_id, name, national_id, role, course, department, sec = record
                label = ctk.CTkLabel(result_window, text=f"ID: {person_id}, Name: {name}, National ID: {national_id}, Role: {role}, Course: {course}, Department: {department}, Sec: {sec}", font=("Arial", 14))
                label.pack(pady=5)

    def check_absences(self):
        name = self.entry_name.get()
        if not name:
            messagebox.showerror("Error", "Please enter a name to check absences.")
            return

        cursor.execute("SELECT id, national_id, role FROM persons WHERE name = ?", (name,))
        result = cursor.fetchone()

        if result:
            person_id, national_id, role = result
            person = Person(name, national_id, role)
            person.id = person_id
            person.check_absence_warning_gui()
        else:
            messagebox.showerror("Error", "Person not found in the database.")

    def student_menu(self):
        self.setup_input_screen("Student",course_options=["AI", "Math", "Cyber", "Machine Learning", "Sound", "OOP", "Electronics", "Logic", "Statics"]  ,department_options=["Department 1", "Department 2", "Department 3", "Department 4"], sec_options=["sec 1", "sec 2", "sec 3", "sec 4"])

    def teacher_menu(self):
        self.setup_input_screen("Teacher",course_options=["AI", "Math", "Cyber", "Machine Learning", "Sound", "OOP", "Electronics", "Logic", "Statics"] , department_options=["Department 1", "Department 2", "Department 3", "Department 4"], sec_options=["sec 1", "sec 2", "sec 3", "sec 4"])

    def admin_menu(self):
        self.setup_input_screen("Admin",department_options= ["Security", "Maintenance", "Cleanliness", "Warehouses"],course_options=None,sec_options=None)
    

    def open_course(self):
        course = self.entry_course.get()
        if not course:
            messagebox.showerror("Error", "Please select a course to open.")
            return

        teacher = Person("Teacher Name", "Teacher ID", "Teacher")  # استبدل بالقيم الفعلية
        try:
            teacher.open_course(course)
            messagebox.showinfo("Success", f"Course '{course}' is now open!")
        except PermissionError as e:
            messagebox.showerror("Error", str(e))

    def close_course(self):
        course = self.entry_course.get()
        if not course:
            messagebox.showerror("Error", "Please select a course to close.")
            return

        teacher = Person("Teacher Name", "Teacher ID", "Teacher")  # استبدل بالقيم الفعلية
        try:
            teacher.close_course(course)
            messagebox.showinfo("Success", f"Course '{course}' is now closed!")
        except PermissionError as e:
            messagebox.showerror("Error", str(e))

    


   # def open_course(self):
   #     course = self.entry_course.get()
    #     self.teacher.open_course(course)

   # def close_course(self):
    #     course = self.entry_course.get()
    #     self.teacher.close_course(course)



    # def open(self, course)
    #     if course:
    #         self.opened_courses.add(course)
    #         messagebox.showinfo("Success", f"Course '{course}' is now open!")
    #     else:
    #         messagebox.showwarning("Error", "Please enter a course name!")

    # def close(self, course):
    #     if course in self.opened_courses:
    #         self.opened_courses.remove(course)
    #         messagebox.showinfo("Success", f"Course '{course}' is now closed!")
    #     else:
    #         messagebox.showwarning("Error", "Course is not currently open!")



# تشغيل التطبيق
root = ctk.CTk()
app = App(root)
root.title("Attendance Registration System")
root.geometry("800x600")
root.mainloop()

# إغلاق الاتصال بقاعدة البيانات عند انتهاء البرنامج
conn.close()