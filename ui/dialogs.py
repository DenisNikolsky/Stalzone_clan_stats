import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import re
from ocr_helper import extract_text_from_image

# ---------- Парсинг ника и реального имени ----------
def parse_nick_and_real(raw_line):
    line = raw_line.strip()
    if not line:
        return None, None
    line = re.sub(r'\[[^\]]*\]', '', line).strip()
    real_name = ""
    matches = re.findall(r'\(([^)]*)\)', line)
    if matches:
        real_name = matches[-1].strip()
        line = re.sub(r'\([^)]*\)', '', line).strip()
    parts = line.split()
    if parts:
        nick = parts[0]
        nick = re.sub(r'[^a-zA-Zа-яА-Я0-9_ .-]', '', nick).strip()
        if len(nick) >= 2:
            return nick, real_name
    return None, None

# ---------- Добавление вручную ----------
def add_member_dialog(app):
    dialog = tk.Toplevel(app.root)
    dialog.title("Добавить участника")
    dialog.geometry("300x200")
    dialog.transient(app.root)
    dialog.grab_set()
    app.theme_manager.apply_to_window(dialog)

    ttk.Label(dialog, text="Игровой ник:").grid(row=0, column=0, padx=5, pady=10)
    entry_name = ttk.Entry(dialog, width=20)
    entry_name.grid(row=0, column=1, padx=5, pady=10)

    ttk.Label(dialog, text="Реальное имя:").grid(row=1, column=0, padx=5, pady=10)
    entry_real = ttk.Entry(dialog, width=20)
    entry_real.grid(row=1, column=1, padx=5, pady=10)

    ttk.Label(dialog, text="Роль:").grid(row=2, column=0, padx=5, pady=10)
    roles = ["офицер", "рядовой", "полковник", "сержант"]
    combo_role = ttk.Combobox(dialog, values=roles, state="readonly", width=18)
    combo_role.set("рядовой")
    combo_role.grid(row=2, column=1, padx=5, pady=10)

    def add():
        name = entry_name.get().strip()
        real_name = entry_real.get().strip()
        role = combo_role.get()
        if not name:
            messagebox.showerror("Ошибка", "Введите игровой ник")
            return
        if app.db.add_member(name, role, real_name):
            app.refresh_list()
            dialog.destroy()
        else:
            messagebox.showerror("Ошибка", f"Участник с ником '{name}' уже существует")

    ttk.Button(dialog, text="Добавить", command=add).grid(row=3, column=0, columnspan=2, pady=10)

# ---------- Добавление из фото (с обновлением существующих) ----------
def add_from_photo(app):
    filenames = filedialog.askopenfilenames(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")])
    if not filenames:
        return
    all_parsed = []
    for filename in filenames:
        try:
            lines = extract_text_from_image(filename)
            if not lines:
                continue
            for raw in lines:
                nick, real = parse_nick_and_real(raw)
                if nick:
                    all_parsed.append((nick, real))
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка при обработке {filename}: {str(e)}")
            return
    if not all_parsed:
        messagebox.showwarning("OCR", "Не найдено ни одного корректного ника")
        return
    unique = {}
    for nick, real in all_parsed:
        if nick not in unique:
            unique[nick] = real
        elif unique[nick] == "" and real:
            unique[nick] = real
    parsed = list(unique.items())
    preview = "\n".join([f"{n} ({r})" if r else n for n, r in parsed[:10]])
    if len(parsed) > 10:
        preview += f"\n... и ещё {len(parsed)-10}"
    if not messagebox.askyesno("Подтверждение", f"Будет добавлено/обновлено {len(parsed)} участников:\n\n{preview}"):
        return
    added = 0
    updated = 0
    skipped = 0
    for nick, real in parsed:
        existing = app.db.get_member(nick)
        if existing:
            if existing['real_name'] == "" and real:
                app.db.update_member(nick, nick, real, existing['role'])
                updated += 1
            else:
                skipped += 1
        else:
            if app.db.add_member(nick, "рядовой", real):
                added += 1
            else:
                skipped += 1
    app.refresh_list()
    messagebox.showinfo("Результат",
                        f"Добавлено новых: {added}\n"
                        f"Обновлено (добавлено реальное имя): {updated}\n"
                        f"Пропущено: {skipped}")

# ---------- Редактирование участника (с сохранением сортировки) ----------
def edit_member_dialog(app, item):
    if not item:
        messagebox.showerror("Ошибка", "Выберите участника")
        return
    display, old_role, warnings = app.tree.item(item, "values")
    if " (" in display:
        old_name = display.split(" (")[0]
        old_real = display.split(" (")[1].rstrip(")")
    else:
        old_name = display
        old_real = ""

    dialog = tk.Toplevel(app.root)
    dialog.title("Редактирование участника")
    dialog.geometry("300x200")
    dialog.transient(app.root)
    dialog.grab_set()
    app.theme_manager.apply_to_window(dialog)

    def on_close():
        app.edit_dialog_open = False
        dialog.destroy()
    dialog.protocol("WM_DELETE_WINDOW", on_close)

    ttk.Label(dialog, text="Игровой ник:").grid(row=0, column=0, padx=5, pady=5)
    entry_name = ttk.Entry(dialog, width=20)
    entry_name.insert(0, old_name)
    entry_name.grid(row=0, column=1, padx=5, pady=5)

    ttk.Label(dialog, text="Реальное имя:").grid(row=1, column=0, padx=5, pady=5)
    entry_real = ttk.Entry(dialog, width=20)
    entry_real.insert(0, old_real)
    entry_real.grid(row=1, column=1, padx=5, pady=5)

    ttk.Label(dialog, text="Роль:").grid(row=2, column=0, padx=5, pady=5)
    roles = ["офицер", "рядовой", "полковник", "сержант"]
    combo_role = ttk.Combobox(dialog, values=roles, state="readonly", width=18)
    combo_role.set(old_role)
    combo_role.grid(row=2, column=1, padx=5, pady=5)

    def save_edit():
        new_name = entry_name.get().strip()
        new_real = entry_real.get().strip()
        new_role = combo_role.get()
        if not new_name:
            messagebox.showerror("Ошибка", "Ник не может быть пустым")
            return
        if new_name != old_name and app.db.get_member(new_name):
            messagebox.showerror("Ошибка", f"Участник с ником '{new_name}' уже существует")
            return
        app.db.update_member(old_name, new_name, new_real, new_role)
        # Обновляем только одну строку, чтобы сохранить сортировку
        new_display = f"{new_name} ({new_real})" if new_real else new_name
        app.tree.item(item, values=(new_display, new_role, warnings))
        app.edit_dialog_open = False
        dialog.destroy()

    ttk.Button(dialog, text="Сохранить", command=save_edit).grid(row=3, column=0, columnspan=2, pady=10)

# ---------- Удаление участников ----------
def remove_members(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showerror("Ошибка", "Выберите хотя бы одного участника")
        return
    names = []
    for item in selected:
        display = app.tree.item(item, "values")[0]
        if " (" in display:
            names.append(display.split(" (")[0])
        else:
            names.append(display)
    if messagebox.askyesno("Подтверждение", f"Удалить {len(names)} участников?\n\n" + "\n".join(names)):
        for name in names:
            app.db.remove_member(name)
        app.refresh_list()

# ---------- Ручное предупреждение ----------
def add_manual_warning(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showerror("Ошибка", "Выберите хотя бы одного участника")
        return
    names = []
    for item in selected:
        display = app.tree.item(item, "values")[0]
        if " (" in display:
            names.append(display.split(" (")[0])
        else:
            names.append(display)

    count_str = simpledialog.askstring(
        "Выдать предупреждения",
        f"Сколько предупреждений выдать для {len(names)} участника(ов)?\n(по умолчанию 1)",
        initialvalue="1"
    )
    if not count_str:
        return
    try:
        count = int(count_str)
        if count <= 0:
            raise ValueError
    except ValueError:
        messagebox.showerror("Ошибка", "Введите положительное целое число")
        return

    reason = simpledialog.askstring(
        "Причина предупреждения",
        "Введите причину (необязательно):",
        initialvalue=""
    )
    if reason is None:
        return
    if not reason.strip():
        reason = "Без причины"

    absent_str = f"Выдано {count} предупреждений для: " + ", ".join(names)
    event_id = app.db.add_event(f"Ручное: {reason}", [absent_str])

    for name in names:
        member_id = app.db.get_member_id_by_name(name)
        if member_id:
            for _ in range(count):
                app.db.add_warning(member_id, event_id, reason)

    app.refresh_list()
    messagebox.showinfo("Готово", f"Выдано {count} предупреждений для {len(names)} участников")

# ---------- Удаление предупреждения ----------
def delete_warning_dialog(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showerror("Ошибка", "Выберите участника")
        return
    item = selected[0]
    display = app.tree.item(item, "values")[0]
    if " (" in display:
        name = display.split(" (")[0]
    else:
        name = display
    member_data = app.db.get_member(name)
    if not member_data:
        messagebox.showerror("Ошибка", "Участник не найден")
        return
    member_id = member_data['id']

    warnings = app.db.get_warnings_for_member(member_id)
    if not warnings:
        messagebox.showinfo("История", f"У {display} нет предупреждений")
        return

    dialog = tk.Toplevel(app.root)
    dialog.title(f"Удаление предупреждений для {display}")
    dialog.geometry("600x300")
    dialog.transient(app.root)
    app.theme_manager.apply_to_window(dialog)

    frame = ttk.Frame(dialog)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame, columns=("Дата", "Событие", "Причина"), show="headings", selectmode='extended')
    tree.heading("Дата", text="Дата")
    tree.heading("Событие", text="Событие")
    tree.heading("Причина", text="Причина")
    tree.column("Дата", width=150)
    tree.column("Событие", width=200)
    tree.column("Причина", width=200)

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    warning_ids = {}
    for w in warnings:
        wid = w['id']
        tree.insert("", "end", values=(w['date'], w['event_type'], w['comment']), tags=(wid,))
        warning_ids[wid] = (w['date'], w['event_type'], w['comment'])

    def delete_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Ошибка", "Выберите предупреждения для удаления")
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить {len(sel)} предупреждений?"):
            return
        for item in sel:
            wid = int(tree.item(item, "tags")[0])
            app.db.delete_warning(wid, member_id)
        app.refresh_list()
        dialog.destroy()
        messagebox.showinfo("Готово", "Предупреждения удалены")

    ttk.Button(dialog, text="Удалить выбранные", command=delete_selected).pack(pady=5)

# ---------- Редактирование предупреждения ----------
def edit_warning_dialog(app):
    selected = app.tree.selection()
    if not selected:
        messagebox.showerror("Ошибка", "Выберите участника")
        return
    item = selected[0]
    display = app.tree.item(item, "values")[0]
    if " (" in display:
        name = display.split(" (")[0]
    else:
        name = display
    member_data = app.db.get_member(name)
    if not member_data:
        messagebox.showerror("Ошибка", "Участник не найден")
        return
    member_id = member_data['id']

    warnings = app.db.get_warnings_for_member(member_id)
    if not warnings:
        messagebox.showinfo("История", f"У {display} нет предупреждений")
        return

    dialog = tk.Toplevel(app.root)
    dialog.title(f"Редактирование предупреждений для {display}")
    dialog.geometry("600x300")
    dialog.transient(app.root)
    app.theme_manager.apply_to_window(dialog)

    frame = ttk.Frame(dialog)
    frame.pack(fill="both", expand=True, padx=10, pady=10)

    tree = ttk.Treeview(frame, columns=("Дата", "Событие", "Причина"), show="headings", selectmode='browse')
    tree.heading("Дата", text="Дата")
    tree.heading("Событие", text="Событие")
    tree.heading("Причина", text="Причина")
    tree.column("Дата", width=150)
    tree.column("Событие", width=200)
    tree.column("Причина", width=200)

    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    warning_map = {}
    for w in warnings:
        wid = w['id']
        tree.insert("", "end", values=(w['date'], w['event_type'], w['comment']), tags=(wid,))
        warning_map[wid] = (w['date'], w['event_type'], w['comment'])

    def edit_selected():
        sel = tree.selection()
        if not sel:
            messagebox.showerror("Ошибка", "Выберите одно предупреждение")
            return
        item = sel[0]
        wid = int(tree.item(item, "tags")[0])
        current_comment = warning_map[wid][2]
        new_comment = simpledialog.askstring(
            "Редактировать причину",
            "Введите новую причину:",
            initialvalue=current_comment
        )
        if new_comment is None:
            return
        if new_comment.strip() == "":
            new_comment = "Без причины"
        app.db.update_warning_comment(wid, new_comment)
        tree.item(item, values=(warning_map[wid][0], warning_map[wid][1], new_comment))
        warning_map[wid] = (warning_map[wid][0], warning_map[wid][1], new_comment)
        app.refresh_list()
        messagebox.showinfo("Готово", "Причина обновлена")

    ttk.Button(dialog, text="Редактировать выбранное", command=edit_selected).pack(pady=5)