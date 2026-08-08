"""Ekran uzerinde ceviri bolgesi secme (surukle-birak).

Pencere, overrideredirect + geometry ile tum sanal masaustunu kaplar
(fullscreen ozelligi overrideredirect ile Windows'ta kullanilamaz).
Donen bolge, sanal masaustu (global) koordinat sistemindedir.
"""
import tkinter as tk

from .screen import virtual_desktop


def select_region(root, monitor_index=0):
    """Kullaniciya ekran uzerinde dikdortgen secim yaptirir.

    Esc veya sag tik ile iptal edilebilir; iptalde None doner.
    """
    vd = virtual_desktop()
    vw = max(1, vd["width"])
    vh = max(1, vd["height"])

    sel = tk.Toplevel(root)
    sel.overrideredirect(True)
    sel.attributes("-topmost", True)
    sel.attributes("-alpha", 0.35)
    sel.configure(bg="black")
    sel.geometry(f"{vw}x{vh}-0-0")

    canvas = tk.Canvas(sel, cursor="crosshair", bg="black",
                       highlightthickness=0)
    canvas.pack(fill="both", expand=True)

    state = {"x0": 0, "y0": 0, "rect": None}
    result = {"done": False, "region": None}

    def on_press(event):
        state["x0"], state["y0"] = event.x_root, event.y_root
        state["rect"] = canvas.create_rectangle(
            event.x_root, event.y_root, event.x_root, event.y_root,
            outline="#00FF00", width=2)

    def on_drag(event):
        if state["rect"] is not None:
            canvas.coords(state["rect"], state["x0"], state["y0"],
                          event.x_root, event.y_root)

    def on_release(event):
        x1, y1 = state["x0"], state["y0"]
        x2, y2 = event.x_root, event.y_root
        left, top = min(x1, x2), min(y1, y2)
        rw, rh = abs(x2 - x1), abs(y2 - y1)
        if rw < 10 or rh < 10:
            result["done"] = True
            sel.destroy()
            return
        result["region"] = {"left": left, "top": top,
                            "width": rw, "height": rh}
        result["done"] = True
        sel.destroy()

    def on_cancel(event):
        result["done"] = True
        sel.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    canvas.bind("<Button-3>", on_cancel)
    canvas.bind("<Escape>", on_cancel)
    canvas.focus_set()
    sel.focus_force()
    sel.grab_set()

    try:
        sel.deiconify()
        sel.lift()
    except tk.TclError:
        pass

    while not result["done"]:
        root.update()
        root.update_idletasks()
    return result["region"]
