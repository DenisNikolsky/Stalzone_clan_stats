import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
from ocr_helper import extract_text_from_image

# ---------- Вспомогательная функция для склонения ----------
def get_accusative(event_type):
    """
    Возвращает событие в винительном падеже для фразы "не пришёл на ..."
    """
    # Словарь исключений
    exceptions = {
        "Потасовка": "Потасовку",
        "Турнир": "Турнир",       # не склоняется? Лучше оставить как есть
        "Gold Drop": "Gold Drop", # не склоняется
        "Другое": "Другое"        # не склоняется
    }
    # Проверяем, есть ли в словаре
    if event_type in exceptions:
        return exceptions[event_type]
    # Если не найдено, возвращаем как есть (или можно попробовать автоматически,
    # но для простоты оставляем)
    return event_type

# ---------- Проведение события ----------
def run_event(app):
    members = app.db.get_all_members()
    if not members:
        messagebox.showinfo("Информация", "В клане нет участников")
        return

    weekday = datetime.now().weekday()
    # По умолчанию ставим "Турнир" в среду, четверг, пятницу, иначе "Потасовка"
    default_event = "Турнир" if weekday in (2, 3, 4) else "Потасовка"

    dialog = tk.Toplevel(app.root)
    dialog.title("Проведение события")
    dialog.geometry("400x500")
    dialog.transient(app.root)
    dialog.grab_set()
    app.theme_manager.apply_to_window(dialog)

    main_frame = ttk.Frame(dialog, style='TFrame')
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)

    ttk.Label(main_frame, text="Тип события:", style='TLabel').pack(pady=5)
    event_types = ["Турнир", "Gold Drop", "Потасовка", "Другое"]
    event_var = tk.StringVar(value=default_event)
    combo_event = ttk.Combobox(main_frame, textvariable=event_var, values=event_types, state="readonly")
    combo_event.pack(pady=5)

    def load_photos():
        filenames = filedialog.askopenfilenames(filetypes=[("Изображения", "*.png *.jpg *.jpeg *.bmp")])
        if not filenames:
            return
        found = set()
        for filename in filenames:
            try:
                lines = extract_text_from_image(filename)
                for name, _, _, _ in members:
                    for line in lines:
                        if name.lower() in line.lower():
                            found.add(name)
                            break
            except Exception as e:
                messagebox.showerror("Ошибка OCR", f"Ошибка при обработке {filename}: {str(e)}")
                return
        if found:
            for name, _, _, _ in members:
                check_vars[name].set(name in found)
            messagebox.showinfo("OCR", f"Отмечено {len(found)} участников из {len(filenames)} фото")
        else:
            messagebox.showwarning("OCR", "Не найдено ни одного ника")

    # Акцентная кнопка для загрузки фото
    style = ttk.Style()
    style.configure('Accent.TButton', foreground='white', background='#3a6ea5', font=('Segoe UI', 10, 'bold'))
    style.map('Accent.TButton', background=[('active', '#4a7eb5')])
    btn_photo = ttk.Button(main_frame, text="📷 Загрузить фото для отметки (можно несколько)",
                           command=load_photos, style='Accent.TButton')
    btn_photo.pack(pady=5)

    ttk.Label(main_frame, text="Отметьте присутствующих:", style='TLabel').pack(pady=5)

    frame_check = ttk.Frame(main_frame, style='TFrame')
    frame_check.pack(fill="both", expand=True, padx=5, pady=5)

    canvas = tk.Canvas(frame_check, highlightthickness=0)
    bg_color = app.theme_manager.colors['bg']
    canvas.configure(bg=bg_color)

    scrollbar = ttk.Scrollbar(frame_check, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas, style='TFrame')

    scrollable_frame.bind(
        "<Configure>",
        lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
    )
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)

    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    check_vars = {}
    for name, real_name, role, _ in members:
        display = f"{name} ({real_name})" if real_name else name
        var = tk.BooleanVar(value=True)
        chk = ttk.Checkbutton(scrollable_frame, text=f"{display} — {role}", variable=var, style='TCheckbutton')
        chk.pack(anchor="w", pady=2)
        check_vars[name] = var

    def confirm(event=None):
        event_type = event_var.get()
        absent_names = []
        for name, _, _, _ in members:
            if not check_vars[name].get():
                absent_names.append(name)
        if absent_names:
            event_id = app.db.add_event(event_type, absent_names)
            for name in absent_names:
                member_id = app.db.get_member_id_by_name(name)
                if member_id:
                    # Используем правильное склонение
                    event_acc = get_accusative(event_type)
                    reason = f"Не пришёл на {event_acc}"
                    app.db.add_warning(member_id, event_id, reason)
            messagebox.showinfo("Предупреждения", "Предупреждения получили:\n" + "\n".join(absent_names))
        else:
            messagebox.showinfo("Информация", "Все участники присутствовали")
        app.refresh_list()
        dialog.destroy()

    btn_confirm = ttk.Button(main_frame, text="Подтвердить", command=confirm, style='TButton')
    btn_confirm.pack(pady=10)
    dialog.bind('<Return>', confirm)
    btn_confirm.focus_set()
    dialog.bind('<Escape>', lambda e: dialog.destroy())


# ---------- Очистка истории ----------
def clear_history(app):
    if not messagebox.askyesno("Подтверждение",
                               "Вы действительно хотите удалить ВСЮ историю событий и связанные с ними предупреждения?\n"
                               "Это действие необратимо."):
        return
    conn = app.db.conn
    c = conn.cursor()
    try:
        c.execute("DELETE FROM warnings")
        c.execute("DELETE FROM events")
        c.execute("UPDATE members SET warnings = 0")
        conn.commit()
        messagebox.showinfo("Готово", "История событий и предупреждений очищена")
        app.refresh_list()
    except Exception as e:
        conn.rollback()
        messagebox.showerror("Ошибка", f"Не удалось очистить историю: {str(e)}")


# ---------- История предупреждений ----------
def show_warning_history(app, event=None):
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
    dialog.title(f"Предупреждения для {display}")
    dialog.geometry("600x300")
    dialog.transient(app.root)
    app.theme_manager.apply_to_window(dialog)

    tree = ttk.Treeview(dialog, columns=("Дата", "Событие", "Причина"), show="headings")
    tree.heading("Дата", text="Дата выдачи")
    tree.heading("Событие", text="Тип события")
    tree.heading("Причина", text="Причина")
    tree.column("Дата", width=150)
    tree.column("Событие", width=200)
    tree.column("Причина", width=200)

    scroll = ttk.Scrollbar(dialog, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    for w in warnings:
        tree.insert("", "end", values=(w['date'], w['event_type'], w['comment']))


# ---------- История событий ----------
def show_history(app):
    history = app.db.get_events(50)
    if not history:
        messagebox.showinfo("История", "Событий пока нет")
        return

    dialog = tk.Toplevel(app.root)
    dialog.title("История событий")
    dialog.geometry("600x400")
    dialog.transient(app.root)
    app.theme_manager.apply_to_window(dialog)

    tree = ttk.Treeview(dialog, columns=("Дата", "Тип", "Отсутствовали"), show="headings")
    tree.heading("Дата", text="Дата и время")
    tree.heading("Тип", text="Тип события")
    tree.heading("Отсутствовали", text="Отсутствовали")
    tree.column("Дата", width=150)
    tree.column("Тип", width=150)
    tree.column("Отсутствовали", width=280)

    scroll = ttk.Scrollbar(dialog, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")

    for date, etype, absent in history:
        tree.insert("", "end", values=(date, etype, absent))