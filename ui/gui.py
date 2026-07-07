import tkinter as tk
from tkinter import ttk, messagebox, filedialog, Menu
import tkinter.font as tkfont
from database import Database
from ui.theme_manager import ThemeManager
from ui.tree_utils import TreeManager
from ui.dialogs import (
    add_member_dialog, add_from_photo, edit_member_dialog,
    remove_members, add_manual_warning, delete_warning_dialog,
    edit_warning_dialog
)
from ui.events import run_event, show_warning_history, show_history, clear_history


class ClanApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Управление кланом Stalcraft")
        self.root.geometry("900x600")
        self.root.minsize(800, 500)

        self.db = Database()
        self.theme_manager = ThemeManager(self.root)

        # Флаги блокировки для предотвращения повторных действий
        self.event_dialog_open = False
        self.edit_dialog_open = False

        self.create_menu()
        self.create_widgets()
        self.create_context_menus()
        self.create_status_bar()

        self.refresh_list()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    # ---------- Меню ----------
    def create_menu(self):
        menubar = Menu(self.root)
        self.root.config(menu=menubar)

        members_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Участники", menu=members_menu)
        members_menu.add_command(label="Добавить нового (вручную)", command=lambda: add_member_dialog(self))
        members_menu.add_command(label="Добавить из фото", command=lambda: add_from_photo(self))
        members_menu.add_separator()
        members_menu.add_command(label="Редактировать выбранного", command=self.edit_member_wrapper)
        members_menu.add_command(label="Удалить выбранных", command=lambda: remove_members(self))
        members_menu.add_separator()
        members_menu.add_command(label="Обновить список", command=self.refresh_list)

        events_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="События", menu=events_menu)
        events_menu.add_command(label="Провести событие", command=self.run_event_wrapper)
        events_menu.add_command(label="История событий", command=lambda: show_history(self))
        events_menu.add_separator()
        events_menu.add_command(label="История предупреждений (выбранного)", command=lambda: show_warning_history(self))
        events_menu.add_separator()
        events_menu.add_command(label="Очистить историю событий", command=lambda: clear_history(self))

        import_export_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Импорт/Экспорт", menu=import_export_menu)
        import_export_menu.add_command(label="Экспорт Excel", command=self.export_excel)
        import_export_menu.add_command(label="Импорт Excel", command=self.import_excel)

        settings_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Настройки", menu=settings_menu)
        settings_menu.add_command(label="Изменить шрифт", command=self.change_font)

        help_menu = Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    # ---------- Виджеты ----------
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, style='TFrame')
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.frame_list = ttk.LabelFrame(main_frame, text="Состав клана (двойной клик – история предупреждений)",
                                         padding=10, style='TLabelframe')
        self.frame_list.pack(fill="both", expand=True)

        columns = ("Участник", "Роль", "Предупреждения")
        self.tree = ttk.Treeview(self.frame_list, columns=columns, show="headings", height=20, selectmode='extended')
        self.tree.heading("Участник", text="Участник (ник / реальное имя)", command=lambda: self.tree_manager.sort_by("Участник"))
        self.tree.heading("Роль", text="Роль", command=lambda: self.tree_manager.sort_by("Роль"))
        self.tree.heading("Предупреждения", text="Предупреждения", command=lambda: self.tree_manager.sort_by("Предупреждения"))
        self.tree.column("Участник", width=400, anchor="w")
        self.tree.column("Роль", width=150, anchor="center")
        self.tree.column("Предупреждения", width=100, anchor="center")

        scrollbar = ttk.Scrollbar(self.frame_list, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.tree_manager = TreeManager(self.tree, self)

        self.tree.bind("<Double-1>", lambda e: show_warning_history(self))
        self.tree.bind("<Button-3>", self.show_context_menu)

    # ---------- Статусная строка ----------
    def create_status_bar(self):
        self.status_var = tk.StringVar()
        self.status_var.set("Всего участников: 0")
        status_label = ttk.Label(self.root, textvariable=self.status_var, style='TLabel', relief='sunken', anchor='w')
        status_label.pack(side='bottom', fill='x', padx=5, pady=2)

    def update_status(self):
        members = self.db.get_all_members()
        count = len(members)
        self.status_var.set(f"Всего участников: {count}")

    # ---------- Контекстные меню ----------
    def create_context_menus(self):
        self.member_menu = Menu(self.root, tearoff=0)
        self.member_menu.add_command(label="Редактировать", command=self.edit_member_wrapper)
        self.member_menu.add_command(label="Удалить", command=lambda: remove_members(self))
        self.member_menu.add_separator()
        self.member_menu.add_command(label="Выдать предупреждение", command=lambda: add_manual_warning(self))
        self.member_menu.add_command(label="Удалить предупреждение", command=lambda: delete_warning_dialog(self))
        self.member_menu.add_command(label="Редактировать предупреждение", command=lambda: edit_warning_dialog(self))
        self.member_menu.add_separator()
        self.member_menu.add_command(label="История предупреждений", command=lambda: show_warning_history(self))

        self.empty_menu = Menu(self.root, tearoff=0)
        self.empty_menu.add_command(label="Добавить нового (вручную)", command=lambda: add_member_dialog(self))
        self.empty_menu.add_command(label="Добавить из фото", command=lambda: add_from_photo(self))

    def show_context_menu(self, event):
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
            self.member_menu.post(event.x_root, event.y_root)
        else:
            self.tree.selection_remove(self.tree.selection())
            self.empty_menu.post(event.x_root, event.y_root)

    # ---------- Обёртки для блокировки ----------
    def run_event_wrapper(self):
        # Если флаг уже True, но окна нет – сбрасываем
        if self.event_dialog_open:
            for child in self.root.winfo_children():
                if isinstance(child, tk.Toplevel) and child.title() == "Проведение события":
                    return  # окно есть, ничего не делаем
            self.event_dialog_open = False  # сброс "залипшего" флага

        members = self.db.get_all_members()
        if not members:
            messagebox.showinfo("Информация", "В клане нет участников")
            return

        self.event_dialog_open = True
        try:
            run_event(self)
        except Exception as e:
            # Если внутри run_event произошла ошибка – сбрасываем флаг
            self.event_dialog_open = False
            raise

    def edit_member_wrapper(self):
        """Блокирует повторное открытие окна редактирования"""
        if self.edit_dialog_open:
            return
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Ошибка", "Выберите участника для редактирования")
            return
        self.edit_dialog_open = True
        item = selected[0]
        edit_member_dialog(self, item)  # Флаг будет сброшен внутри диалога

    # ---------- Обновление списка ----------
    def refresh_list(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for name, real_name, role, warnings in self.db.get_all_members():
            display_name = f"{name} ({real_name})" if real_name else name
            self.tree.insert("", "end", values=(display_name, role, warnings))
        self.update_status()

    # ---------- Настройка шрифта ----------
    def change_font(self):
        dialog = tk.Toplevel(self.root)
        dialog.title("Настройка шрифта")
        dialog.geometry("320x160")
        dialog.transient(self.root)
        dialog.grab_set()
        self.theme_manager.apply_to_window(dialog)

        frame = ttk.Frame(dialog, style='TFrame')
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Шрифт:", style='TLabel').grid(row=0, column=0, padx=5, pady=5, sticky='e')
        fonts = list(tkfont.families())
        combo_font = ttk.Combobox(frame, values=fonts, state="readonly", width=22)
        combo_font.set(self.theme_manager.font_family)
        combo_font.grid(row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Размер:", style='TLabel').grid(row=1, column=0, padx=5, pady=5, sticky='e')
        spin_size = ttk.Spinbox(frame, from_=8, to=24, width=5)
        spin_size.set(self.theme_manager.font_size)
        spin_size.grid(row=1, column=1, padx=5, pady=5, sticky='w')

        def apply_font():
            family = combo_font.get()
            try:
                size = int(spin_size.get())
            except ValueError:
                size = 10
            self.theme_manager.set_font(family, size)
            self.theme_manager.apply_to_window(dialog)
            dialog.destroy()

        ttk.Button(frame, text="Применить", command=apply_font, style='TButton').grid(row=2, column=0, columnspan=2, pady=10)

    # ---------- Импорт / Экспорт Excel ----------
    def export_excel(self):
        filename = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
        if filename:
            try:
                from ui.excel_utils import export_to_excel
                export_to_excel(self.db, filename)
                messagebox.showinfo("Экспорт", f"Экспортировано в {filename}")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    def import_excel(self):
        filename = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx")])
        if filename:
            try:
                from ui.excel_utils import import_from_excel
                count = import_from_excel(self.db, filename)
                self.refresh_list()
                messagebox.showinfo("Импорт", f"Импортировано {count} участников")
            except Exception as e:
                messagebox.showerror("Ошибка", str(e))

    # ---------- Справка ----------
    def show_about(self):
        messagebox.showinfo("О программе",
            "Управление кланом Stalcraft\n\n"
            "Версия 3.2\n"
            "Новое:\n"
            "- Блокировка повторных действий (события, редактирование)\n"
            "- Редактирование без сброса сортировки\n"
            "- Импорт/экспорт в Excel\n\n"
            "Особенности:\n"
            "- Добавление участников вручную и из фото (OCR)\n"
            "- Проведение событий (Турнир, Gold Drop, Потасовка и др.)\n"
            "- Автоматическое и ручное управление предупреждениями\n"
            "- История событий и предупреждений\n"
            "- Сортировка и выделение (перетаскивание, Ctrl/Shift)\n"
            "- Контекстное меню (правая кнопка мыши)\n\n"
            "База данных: SQLite\n"
            "OCR: Tesseract\n"
            "Автор: Abibas_Karabas")

    # ---------- Закрытие ----------
    def on_closing(self):
        self.db.close()
        self.root.destroy()