import sqlite3
import csv
from datetime import datetime
import threading
import time
import sys
import os

def get_app_path():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.abspath(".")

class Database:
    def __init__(self, db_name="clan.db"):
        self.db_name = os.path.join(get_app_path(), db_name)
        self.lock = threading.Lock()
        self.conn = None
        self._connect()
        self.init_db()
        self.migrate_db()

    def _connect(self):
        self.conn = sqlite3.connect(self.db_name, timeout=10.0)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA busy_timeout=5000")
        self.conn.row_factory = sqlite3.Row

    def _execute(self, query, params=()):
        with self.lock:
            attempts = 0
            while attempts < 5:
                try:
                    cursor = self.conn.cursor()
                    cursor.execute(query, params)
                    self.conn.commit()
                    return cursor
                except sqlite3.OperationalError as e:
                    if "database is locked" in str(e):
                        attempts += 1
                        time.sleep(0.5 * attempts)
                    else:
                        raise
            raise sqlite3.OperationalError("Не удалось выполнить запрос после нескольких попыток")

    def init_db(self):
        self._execute('''
                      CREATE TABLE IF NOT EXISTS members
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          name
                          TEXT
                          UNIQUE
                          NOT
                          NULL,
                          real_name
                          TEXT,
                          role
                          TEXT
                          NOT
                          NULL,
                          warnings
                          INTEGER
                          DEFAULT
                          0
                      )
                      ''')
        self._execute('''
                      CREATE TABLE IF NOT EXISTS events
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          event_date
                          TEXT
                          NOT
                          NULL,
                          event_type
                          TEXT
                          NOT
                          NULL,
                          absentees
                          TEXT
                      )
                      ''')
        self._execute('''
                      CREATE TABLE IF NOT EXISTS warnings
                      (
                          id
                          INTEGER
                          PRIMARY
                          KEY
                          AUTOINCREMENT,
                          member_id
                          INTEGER
                          NOT
                          NULL,
                          event_id
                          INTEGER
                          NOT
                          NULL,
                          date
                          TEXT
                          NOT
                          NULL,
                          comment
                          TEXT
                          DEFAULT
                          '',
                          FOREIGN
                          KEY
                      (
                          member_id
                      ) REFERENCES members
                      (
                          id
                      ) ON DELETE CASCADE,
                          FOREIGN KEY
                      (
                          event_id
                      ) REFERENCES events
                      (
                          id
                      )
                        ON DELETE CASCADE
                          )
                      ''')

    def migrate_db(self):
        cursor = self._execute("PRAGMA table_info(warnings)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'comment' not in columns:
            self._execute("ALTER TABLE warnings ADD COLUMN comment TEXT DEFAULT ''")
        cursor = self._execute("PRAGMA table_info(members)")
        columns = [row['name'] for row in cursor.fetchall()]
        if 'real_name' not in columns:
            self._execute("ALTER TABLE members ADD COLUMN real_name TEXT")

    # ---------- Участники ----------
    def add_member(self, name, role, real_name=""):
        try:
            self._execute(
                "INSERT INTO members (name, real_name, role, warnings) VALUES (?, ?, ?, 0)",
                (name, real_name, role)
            )
            return True
        except sqlite3.IntegrityError:
            return False

    def remove_member(self, name):
        self._execute("DELETE FROM members WHERE name = ?", (name,))

    def update_member(self, old_name, new_name, new_real_name, new_role):
        self._execute(
            "UPDATE members SET name = ?, real_name = ?, role = ? WHERE name = ?",
            (new_name, new_real_name, new_role, old_name)
        )

    def get_all_members(self):
        cursor = self._execute("SELECT name, real_name, role, warnings FROM members ORDER BY name")
        return cursor.fetchall()

    def get_member(self, name):
        cursor = self._execute(
            "SELECT id, name, real_name, role, warnings FROM members WHERE name = ?",
            (name,)
        )
        return cursor.fetchone()

    def get_member_id_by_name(self, name):
        cursor = self._execute("SELECT id FROM members WHERE name = ?", (name,))
        row = cursor.fetchone()
        return row['id'] if row else None

    def increment_warnings_count(self, member_id, amount=1):
        self._execute("UPDATE members SET warnings = warnings + ? WHERE id = ?", (amount, member_id))

    # ---------- События и предупреждения ----------
    def add_event(self, event_type, absentees):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        absent_str = ", ".join(absentees) if absentees else "Все присутствовали"
        cursor = self._execute(
            "INSERT INTO events (event_date, event_type, absentees) VALUES (?, ?, ?)",
            (date_str, event_type, absent_str)
        )
        return cursor.lastrowid

    def add_warning(self, member_id, event_id, comment=""):
        date_str = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._execute(
            "INSERT INTO warnings (member_id, event_id, date, comment) VALUES (?, ?, ?, ?)",
            (member_id, event_id, date_str, comment)
        )
        self.increment_warnings_count(member_id, 1)

    def get_warnings_for_member(self, member_id):
        cursor = self._execute('''
                               SELECT w.id, w.date, e.event_type, w.comment
                               FROM warnings w
                                        JOIN events e ON w.event_id = e.id
                               WHERE w.member_id = ?
                               ORDER BY w.date DESC
                               ''', (member_id,))
        return cursor.fetchall()

    def delete_warning(self, warning_id, member_id):
        self._execute("DELETE FROM warnings WHERE id = ?", (warning_id,))
        cursor = self._execute("SELECT COUNT(*) FROM warnings WHERE member_id = ?", (member_id,))
        count = cursor.fetchone()[0]
        self._execute("UPDATE members SET warnings = ? WHERE id = ?", (count, member_id))

    def update_warning_comment(self, warning_id, new_comment):
        self._execute("UPDATE warnings SET comment = ? WHERE id = ?", (new_comment, warning_id))

    def get_events(self, limit=50):
        cursor = self._execute(
            "SELECT event_date, event_type, absentees FROM events ORDER BY id DESC LIMIT ?",
            (limit,)
        )
        return cursor.fetchall()

    # ---------- Импорт / Экспорт Excel ----------
    def export_to_excel(self, filename):
        """Экспортирует всех участников в Excel-файл"""
        rows = self.get_all_members()
        wb = Workbook()
        ws = wb.active
        ws.title = "Участники"

        # Заголовки
        headers = ["Ник", "Реальное имя", "Роль", "Предупреждения"]
        ws.append(headers)

        # Стили для заголовков
        header_font = Font(bold=True)
        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center')

        # Данные
        for row in rows:
            ws.append([row['name'], row['real_name'], row['role'], row['warnings']])

        # Автоширина колонок
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 40)
            ws.column_dimensions[column_letter].width = adjusted_width

        wb.save(filename)

    def import_from_excel(self, filename):
        """Импортирует участников из Excel-файла. Ожидает колонки: Ник, Реальное имя, Роль, Предупреждения (последняя необязательна)"""
        wb = load_workbook(filename)
        ws = wb.active
        count = 0
        conn = sqlite3.connect(self.db_name)
        c = conn.cursor()
        for row in ws.iter_rows(min_row=2, values_only=True):  # пропускаем заголовок
            if len(row) >= 3 and row[0]:
                name = str(row[0]).strip()
                real_name = str(row[1]).strip() if len(row) > 1 else ""
                role = str(row[2]).strip()
                warnings = int(row[3]) if len(row) > 3 and row[3] is not None else 0
                try:
                    c.execute("INSERT INTO members (name, real_name, role, warnings) VALUES (?, ?, ?, ?)",
                              (name, real_name, role, warnings))
                    count += 1
                except sqlite3.IntegrityError:
                    pass
        conn.commit()
        conn.close()
        return count

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None