import tkinter as tk
from tkinter import ttk

class TreeManager:
    def __init__(self, tree, app):
        self.tree = tree
        self.app = app
        self.drag_start_item = None
        self.drag_start_index = None
        self.drag_selection_set = False
        self.reverse_sort = False

        self._bind_events()

    def _bind_events(self):
        self.tree.bind("<Button-1>", self._on_left_click)
        self.tree.bind("<B1-Motion>", self._on_left_drag)
        self.tree.bind("<ButtonRelease-1>", self._on_left_release)

    def _on_left_click(self, event):
        item = self.tree.identify_row(event.y)
        if not item:
            self.tree.selection_remove(self.tree.selection())
            self.drag_start_item = None
            self.drag_selection_set = False
            return
        state = event.state & 0x0004  # Ctrl
        shift = event.state & 0x0001  # Shift
        if state or shift:
            self.drag_start_item = None
            self.drag_selection_set = False
            return
        self.drag_start_item = item
        self.drag_start_index = self.tree.index(item)
        self.drag_selection_set = True
        self.tree.selection_set(item)

    def _on_left_drag(self, event):
        if not self.drag_selection_set or self.drag_start_item is None:
            return
        item = self.tree.identify_row(event.y)
        if not item:
            return
        current_index = self.tree.index(item)
        start_index = self.drag_start_index
        all_items = self.tree.get_children()
        min_idx = min(start_index, current_index)
        max_idx = max(start_index, current_index)
        to_select = all_items[min_idx:max_idx+1]
        self.tree.selection_set(to_select)

    def _on_left_release(self, event):
        self.drag_start_item = None
        self.drag_selection_set = False

    def sort_by(self, col):
        items = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
        if col == "Предупреждения":
            items.sort(key=lambda x: int(x[0]) if x[0].isdigit() else 0, reverse=self.reverse_sort)
        else:
            items.sort(key=lambda x: x[0].lower(), reverse=self.reverse_sort)
        for index, (_, child) in enumerate(items):
            self.tree.move(child, '', index)
        self.reverse_sort = not self.reverse_sort