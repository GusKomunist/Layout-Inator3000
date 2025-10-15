import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import ezdxf
from shapely.geometry import Polygon, Point
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt

# --- Параметри панелей (готові моделі) ---
PANELS = {
    "Longi 465-675W (1.134×1.8)": (1.134, 1.8),
    "Longi 640-645W (1.134×2.832)": (1.134, 2.832),   
}

# --- Глобальні змінні ---
current_polygon = None
panel_points = []
selected_panel = "Longi 465-675W (1.134×1.8)"
panel_spacing = 0.03   # 30 мм
edge_offset = 0.2      # за замовчуванням 0.2 м
canvas_widget = None
fig, ax = plt.subplots(figsize=(6, 6))

# --- Логіка ---
def import_dwg():
    global current_polygon
    file_path = filedialog.askopenfilename(filetypes=[("DWG/DXF files", "*.dwg *.dxf")])
    if not file_path:
        return

    try:
        doc = ezdxf.readfile(file_path)
        msp = doc.modelspace()
        for e in msp.query("LWPOLYLINE"):
            if e.closed:
                pts = [(p[0], p[1]) for p in e.get_points()]
                current_polygon = Polygon(pts)
                break
        if current_polygon is None:
            messagebox.showerror("Помилка", "Не знайдено замкнених полігонів!")
            return
        place_panels()
        visualize_layout()
    except Exception as e:
        messagebox.showerror("Помилка", str(e))

def create_manual_polygon():
    global current_polygon
    try:
        width = float(entry_width.get())
        height = float(entry_height.get())
        if width <= 0 or height <= 0:
            messagebox.showerror("Помилка", "Розміри повинні бути додатні.")
            return
        current_polygon = Polygon([
            (0, 0), (width, 0), (width, height), (0, height)
        ])
        place_panels()
        visualize_layout()
    except ValueError:
        messagebox.showerror("Помилка", "Введіть числові значення для розмірів.")

def place_panels():
    global panel_points
    if current_polygon is None:
        return

    pw, ph = PANELS[selected_panel]
    minx, miny, maxx, maxy = current_polygon.bounds
    panel_points = []

    y = miny + edge_offset + ph / 2
    while y + ph / 2 <= maxy - edge_offset:
        x = minx + edge_offset + pw / 2
        while x + pw / 2 <= maxx - edge_offset:
            panel = Polygon([
                (x - pw/2, y - ph/2),
                (x + pw/2, y - ph/2),
                (x + pw/2, y + ph/2),
                (x - pw/2, y + ph/2)
            ])
            if current_polygon.contains(panel):
                panel_points.append(Point(x, y))
            x += pw + panel_spacing
        y += ph + panel_spacing

def visualize_layout():
    global canvas_widget
    ax.clear()

    if current_polygon is not None:
        x, y = current_polygon.exterior.xy
        ax.plot(x, y, 'k-')
        pw, ph = PANELS[selected_panel]
        for p in panel_points:
            rect = plt.Rectangle(
                (p.x - pw / 2, p.y - ph / 2),
                pw, ph,
                fill=False, edgecolor='blue', linewidth=0.7
            )
            ax.add_patch(rect)
    ax.axis('equal')
    ax.set_title(f"Візуалізація ({selected_panel})")
    ax.set_xlabel("X, м")
    ax.set_ylabel("Y, м")
    fig.tight_layout()
    canvas_widget.draw()

def export_dwg():
    if current_polygon is None or not panel_points:
        messagebox.showerror("Помилка", "Немає даних для експорту.")
        return

    pw, ph = PANELS[selected_panel]
    file_path = filedialog.asksaveasfilename(defaultextension=".dxf", filetypes=[("DXF files", "*.dxf")])
    if not file_path:
        return

    doc = ezdxf.new()
    msp = doc.modelspace()
    x, y = current_polygon.exterior.xy
    msp.add_lwpolyline(list(zip(x, y)), close=True)

    for p in panel_points:
        x0, y0 = p.x - pw / 2, p.y - ph / 2
        rect = [(x0, y0), (x0 + pw, y0), (x0 + pw, y0 + ph), (x0, y0 + ph)]
        msp.add_lwpolyline(rect, close=True)

    doc.saveas(file_path)
    messagebox.showinfo("Експорт", f"Файл збережено: {file_path}")

def change_panel(event):
    global selected_panel
    selected_panel = combo_panel.get()
    place_panels()
    visualize_layout()

def change_offset(event=None):
    global edge_offset
    try:
        edge_offset = float(entry_offset.get())
        place_panels()
        visualize_layout()
    except ValueError:
        pass

# --- GUI ---
root = tk.Tk()
root.title("Розкладка-Інатор 3000")
root.geometry("1100x700")

# --- Ліва панель керування ---
frame_controls = tk.Frame(root, padx=10, pady=10)
frame_controls.pack(side="left", fill="y")

tk.Label(frame_controls, text="Імпорт / Введення даних", font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
tk.Button(frame_controls, text="Імпортувати DWG/DXF", command=import_dwg, width=25).pack(pady=2)
tk.Label(frame_controls, text="або створити вручну:", font=("Arial", 9)).pack(anchor="w")
tk.Label(frame_controls, text="Ширина (м):").pack(anchor="w")
entry_width = tk.Entry(frame_controls, width=10)
entry_width.insert(0, "10")
entry_width.pack(pady=1, anchor="w")

tk.Label(frame_controls, text="Довжина (м):").pack(anchor="w")
entry_height = tk.Entry(frame_controls, width=10)
entry_height.insert(0, "10")
entry_height.pack(pady=1, anchor="w")

tk.Button(frame_controls, text="Задати свої параметри", command=create_manual_polygon, width=25).pack(pady=5)

tk.Label(frame_controls, text="Вибір панелі:", font=("Arial", 10, "bold")).pack(anchor="w", pady=(10, 0))
combo_panel = ttk.Combobox(frame_controls, values=list(PANELS.keys()), state="readonly", width=25)
combo_panel.set(selected_panel)
combo_panel.bind("<<ComboboxSelected>>", change_panel)
combo_panel.pack(pady=3)

tk.Label(frame_controls, text="Відступ від краю (м):").pack(anchor="w")
entry_offset = tk.Entry(frame_controls, width=10)
entry_offset.insert(0, str(edge_offset))
entry_offset.bind("<Return>", change_offset)
entry_offset.pack(pady=2, anchor="w")

tk.Button(frame_controls, text="Експорт DXF", command=export_dwg, width=25).pack(pady=15)

# --- Права частина — Canvas для візуалізації ---
frame_canvas = tk.Frame(root)
frame_canvas.pack(side="right", expand=True, fill="both")

canvas_widget = FigureCanvasTkAgg(fig, master=frame_canvas)
canvas_widget.get_tk_widget().pack(fill="both", expand=True)

visualize_layout()
root.mainloop()
