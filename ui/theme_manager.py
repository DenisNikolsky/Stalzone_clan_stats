import tkinter as tk
from tkinter import ttk


class ThemeManager:
    def __init__(self, root):
        self.root = root
        self.style = ttk.Style()
        self.style.theme_use('clam')

        # Цветовая схема (тёмная, приятная)
        self.colors = {
            'bg': '#2b2b2b',  # основной фон
            'fg': '#f0f0f0',  # цвет текста
            'select': '#3a6ea5',  # выделение
            'frame_bg': '#3c3c3c',  # фон рамок
            'tree_bg': '#333333',  # фон таблицы
            'button_bg': '#3c3c3c',  # фон кнопки
            'button_active': '#4a4a4a',  # фон кнопки при наведении
            'button_fg': '#f0f0f0',  # текст кнопки
            'button_border': '#5a5a5a'  # цвет рамки кнопки
        }

        self.font_family = 'Segoe UI'
        self.font_size = 10
        self.apply_theme()

    def apply_theme(self):
        # Основные стили
        self.style.configure('TFrame', background=self.colors['bg'])
        self.style.configure('TLabel', background=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('TButton', background=self.colors['button_bg'],
                             foreground=self.colors['button_fg'], borderwidth=1, relief='solid')
        self.style.configure('TLabelframe', background=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('TLabelframe.Label', background=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('Treeview', background=self.colors['tree_bg'],
                             foreground=self.colors['fg'], fieldbackground=self.colors['tree_bg'])
        self.style.configure('Treeview.Heading', background=self.colors['bg'],
                             foreground=self.colors['fg'])
        self.style.configure('TCombobox', fieldbackground=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('TSpinbox', fieldbackground=self.colors['bg'], foreground=self.colors['fg'])
        self.style.configure('TEntry', fieldbackground=self.colors['bg'], foreground=self.colors['fg'])

        # Настройка кнопок при наведении и нажатии (подсветка по краям)
        self.style.map('TButton',
                       background=[('active', self.colors['button_active']),
                                   ('pressed', self.colors['button_active'])],
                       foreground=[('active', self.colors['button_fg'])],
                       bordercolor=[('active', self.colors['button_border']),
                                    ('pressed', self.colors['button_border'])],
                       relief=[('active', 'solid'), ('pressed', 'sunken')])

        # Акцентная кнопка для событий (синяя)
        self.style.configure('Accent.TButton', background='#3a6ea5', foreground='white',
                             borderwidth=1, relief='solid')
        self.style.map('Accent.TButton',
                       background=[('active', '#4a7eb5'), ('pressed', '#2a5e95')],
                       bordercolor=[('active', '#6a9ed5')],
                       relief=[('active', 'solid'), ('pressed', 'sunken')])

        # Применяем шрифт
        font = (self.font_family, self.font_size)
        self.style.configure('TLabel', font=font)
        self.style.configure('TButton', font=font)
        self.style.configure('TLabelframe.Label', font=font)
        self.style.configure('Treeview', font=font)
        self.style.configure('Treeview.Heading', font=font)
        self.style.configure('TCombobox', font=font)
        self.style.configure('TSpinbox', font=font)
        self.style.configure('TEntry', font=font)

        # Фон корневого окна
        self.root.configure(bg=self.colors['bg'])

        # Применяем ко всем дочерним окнам
        self.apply_to_all_windows()

    def apply_to_all_windows(self):
        for window in [self.root] + self.root.winfo_children():
            if isinstance(window, tk.Toplevel):
                self.apply_to_window(window)
            elif isinstance(window, tk.Tk):
                self.apply_to_window(window)

    def apply_to_window(self, window):
        """Рекурсивно применяет стиль ко всем виджетам в окне"""
        try:
            for child in window.winfo_children():
                if isinstance(child, (ttk.Frame, ttk.LabelFrame, ttk.Label,
                                      ttk.Button, ttk.Treeview, ttk.Combobox,
                                      ttk.Entry, ttk.Spinbox)):
                    try:
                        # Применяем стиль, если виджет его поддерживает
                        if isinstance(child, ttk.Button):
                            # Если кнопка с особым стилем, оставляем его
                            current_style = child.cget('style')
                            if current_style and current_style != 'TButton':
                                child.configure(style=current_style)
                            else:
                                child.configure(style='TButton')
                        else:
                            child.configure(style=child.winfo_class())
                    except:
                        pass
                # Рекурсивно обходим вложенные
                if isinstance(child, (tk.Frame, ttk.Frame, ttk.LabelFrame)):
                    self.apply_to_window(child)
        except:
            pass

    def set_font(self, family, size):
        self.font_family = family
        self.font_size = size
        self.apply_theme()

    def get_font(self):
        return (self.font_family, self.font_size)