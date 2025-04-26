import threading
from tkinter import *
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import json

class AppDesign(Tk):
    def __init__(self):
        Tk.__init__(self)
        self.geometry('1100x680+135+0')
        self.configure(bg='white')
        self.title("Logic Circuit Designer")
        self.withdraw()

        # Sidebar and Canvas setup
        self.sidebar = Frame(self, width=150, bg="white")
        self.sidebar.pack(side="left", fill="y")

        self.bottombar = Frame(self, height=200, bg="white")
        self.bottombar.pack(side="bottom", fill='x')

        self.canvas = Canvas(self, width=850, height=700, bg="lightgray")
        self.canvas.pack(fill="both", expand=True)

        # Gate image paths
        self.GATE_IMAGES = {
            "AND": "resources/AND_Gate.png",
            "OR": "resources/OR_Gate.png",
            "NOT": "resources/NOT_Gate.png",
            "NAND": "resources/NAND_Gate.png",
            "NOR": "resources/NOR_Gate.png",
            "XOR": "resources/XOR_Gate.png",
            "XNOR": "resources/XNOR_Gate.png",
            "LAMP": "resources/LAMP_off.png",
            "INPUT_0": "resources/Input_0.png",
            "INPUT_1": "resources/Input_1.png",
            "LAMP_ON": "resources/LAMP_on.png"
        }

        # Load all images
        self.gate_photos = {name: ImageTk.PhotoImage(Image.open(path).resize((60, 60))) for name, path in
                       self.GATE_IMAGES.items()}

        # Globals
        self.gates = []
        self.gate_data = {}
        self.drag_data = {"x": 0, "y": 0, "item": None}
        self.current_drag_image = None
        self.current_drag_name = None
        self.start_point = None
        self.current_line = None
        self.hover_point = None
        self.wires = []
        self.simulation_running = False
        self.delete_mode = False


        # Button to activate/deactivate logic
        self.play_img = Image.open(r'resources/play.png')
        self.play_img = self.play_img.resize((53, 53))
        self.play = ImageTk.PhotoImage(self.play_img)
        self.play_show = Button(self.bottombar, image=self.play, border=False, highlightcolor='black', highlightthickness=False,
                                command=lambda: AppFunctions.toggle_simulation(self))
        self.play_show.pack(side='right', padx=20, pady=5)

        self.pause_img = Image.open(r'resources/pause.png')
        self.pause_img = self.pause_img.resize((53, 53))
        self.pause = ImageTk.PhotoImage(self.pause_img)

        self.disposal_img = Image.open(r'resources/disposal.png')
        self.disposal_img = self.disposal_img.resize((48, 48))
        self.disposal = ImageTk.PhotoImage(self.disposal_img)

        self.delete_img = Image.open(r'resources/delete.png')
        self.delete_img = self.delete_img.resize((40, 40))
        self.delete = ImageTk.PhotoImage(self.delete_img)

        self.save_img = Image.open(r'resources/save.png')
        self.save_img = self.save_img.resize((40, 40))
        self.save = ImageTk.PhotoImage(self.save_img)
        self.save_show = Button(self.bottombar, image=self.save, border=False, highlightcolor='black', highlightthickness=False,
                                command=lambda: AppFunctions.save_circuit(self))
        self.save_show.pack(side='right', padx=20, pady=5)

        self.load_img = Image.open(r'resources/load.png')
        self.load_img = self.load_img.resize((40, 40))
        self.load = ImageTk.PhotoImage(self.load_img)
        self.load_show = Button(self.bottombar, image=self.load, border=False, highlightcolor='black', highlightthickness=False,
                                command=lambda: AppFunctions.load_circuit(self))
        self.load_show.pack(side='right', padx=20, pady=5)

        self.delete_show = Button(self.bottombar, image=self.delete, border=False, highlightcolor='black',
                                  highlightthickness=False, command=lambda: AppFunctions.toggle_delete(self))
        self.delete_show.pack(side='right', padx=20, pady=5)

        self.info = Label(self.bottombar, fg='red', font=('Arial', 20))
        self.info.pack(side='right', padx=10, pady=5)


class AppFunctions:
    @staticmethod
    # دالة لتحريك صورة الـ GIF
    def animate_gif(label, gif, frame=0):
            # تحديث الصورة بإطار جديد في كل مرة
            gif.seek(frame)
            frame_image = ImageTk.PhotoImage(gif)
            label.config(image=frame_image)
            label.image = frame_image

            # الانتقال إلى الإطار التالي بعد 100 مللي ثانية (سرعة الحركة)
            label.after(5, AppFunctions.animate_gif, label, gif, (frame + 1) % gif.n_frames)

    # دالة لعرض نافذة التحميل
    @staticmethod
    def show_loading_window(root):
            loading_window = Toplevel(root)
            loading_window.overrideredirect(True)
            loading_window.geometry("700x400+350+200")

            # تحميل صورة GIF
            gif = Image.open(r"resources/Loading_logo.gif")  # استبدل "loading.gif" باسم ملفك

            # عرض أول إطار من الصورة
            label = Label(loading_window)
            label.pack(expand=True)

            # بدء حركة الـ GIF
            AppFunctions.animate_gif(label, gif)

            # بعد 5 ثوانٍ، يتم إغلاق نافذة التحميل وفتح الرئيسية
            loading_window.after(5000, lambda: AppFunctions.open_main_window(root, loading_window))

    # دالة لفتح النافذة الرئيسية
    @staticmethod
    def open_main_window(root, loading_window):
            loading_window.destroy()  # إغلاق نافذة التحميل
            root.deiconify()  # إظهار النافذة الرئيسية

    @staticmethod
    def toggle_simulation(self=None):
            self.simulation_running = not self.simulation_running
            if self.simulation_running:
                self.play_show.config(image=self.pause)
            else:
                self.play_show.config(image=self.play)

            if self.simulation_running:
                AppFunctions.run_simulation(self)
            else:
                for line_id, p1, p2 in self.wires:
                    self.canvas.itemconfig(line_id, fill="black")

                for gate in self.gates:
                    tags = self.canvas.gettags(gate)
                    if tags[1] == "LAMP":
                        data = self.gate_data[gate]
                        input_points = [p for p in data["points"] if "input" in self.canvas.gettags(p)]
                        if input_points:
                            self.canvas.itemconfig(gate, image=self.gate_photos["LAMP"])


    @staticmethod
    def run_simulation(self=None):
        if not self.simulation_running:
            return

        point_values = {}
        input_links = {}

        # ربط نقاط الإدخال بنقاط الإخراج اللي واصلة ليها
        for line_id, from_point, to_point in self.wires:
            if "output" in self.canvas.gettags(from_point) and "input" in self.canvas.gettags(to_point):
                input_links[to_point] = from_point
            elif "input" in self.canvas.gettags(from_point) and "output" in self.canvas.gettags(to_point):
                input_links[from_point] = to_point

        # تحديد قيم الـ INPUTs
        for gate in self.gates:
            tags = self.canvas.gettags(gate)
            name = tags[1]
            data = self.gate_data[gate]
            output = next((p for p in data["points"] if "output" in self.canvas.gettags(p)), None)

            if name == "INPUT_0" and output:
                point_values[output] = 0
            elif name == "INPUT_1" and output:
                point_values[output] = 1

            print(f'tags: {tags}, name: {name}, data: {data}, output: {output}')

        # تكرار الحساب لنشر الإشارات في الدائرة
        for _ in range(10):
            for gate in self.gates:
                tags = self.canvas.gettags(gate)
                name = tags[1]
                if name in ["INPUT_0", "INPUT_1"]:
                    continue  # 💡 مهم جداً: ما نحسبش INPUT تانيا
                data = self.gate_data[gate]
                inputs = [p for p in data["points"] if "input" in self.canvas.gettags(p)]
                output = next((p for p in data["points"] if "output" in self.canvas.gettags(p)), None)

                def resolve_input(p):
                    src = input_links.get(p)
                    return point_values.get(src, 0) if src else 0

                in_vals = [resolve_input(inp) for inp in inputs]
                print(f'in_vals:{in_vals}, inputs:{inputs}')

                result = 0
                if name == "AND":
                    result = int(all(in_vals))
                elif name == "OR":
                    result = int(any(in_vals))
                elif name == "NOT":
                    result = int(not in_vals[0]) if in_vals else 0
                elif name == "NAND":
                    result = int(not all(in_vals))
                elif name == "NOR":
                    result = int(not any(in_vals))
                elif name == "XOR":
                    result = int(in_vals[0] ^ in_vals[1]) if len(in_vals) >= 2 else 0
                elif name == "XNOR":
                    result = int(not (in_vals[0] ^ in_vals[1])) if len(in_vals) >= 2 else 0

                if output:
                    point_values[output] = result

        # تلوين الأسلاك حسب الإشارة
        for line_id, from_point, to_point in self.wires:
            value = point_values.get(from_point, 0)
            self.canvas.itemconfig(line_id, fill="red" if value else "black")

        # تحديث شكل اللمبات
        for gate in self.gates:
            tags = self.canvas.gettags(gate)
            if tags[1] == "LAMP":
                data = self.gate_data[gate]
                inputs = [p for p in data["points"] if "input" in self.canvas.gettags(p)]

                def resolve_input(p, self=None):
                    src = input_links.get(p)
                    return point_values.get(src, 0) if src else 0

                if inputs:
                    value = resolve_input(inputs[0], self)
                    self.canvas.itemconfig(gate, image=self.gate_photos["LAMP_ON"] if value else self.gate_photos["LAMP"])
                    print("LAMP connected to => Value received:", value)

        # إعادة المحاكاة بعد نصف ثانية
        if self.simulation_running:
            root.after(500, lambda: AppFunctions.run_simulation(self))

        print("=== POINT VALUES ===")
        for k, v in point_values.items():
            print("Point ID:", k, "Value:", v)

    @staticmethod
    def create_gate(name, x, y, self=None):
        image = self.gate_photos[name]
        gate = self.canvas.create_image(x, y, image=image, anchor="nw", tags=("gate", name))

        points = []

        if name == "NOT":
            points.append(self.canvas.create_oval(x + 7, y + 22, x + 17, y + 32, fill="#F1B9B9", tags=("point", "input")))
            out = self.canvas.create_oval(x + 42, y + 23, x + 52, y + 33, fill="#BBF1B9", tags=("point", "output"))
            points.append(out)

        elif name == "LAMP":
            points.append(self.canvas.create_oval(x + 26, y + 42, x + 36, y + 52, fill="#F1B9B9", tags=("point", "input")))

        elif name.startswith("INPUT"):
            out = self.canvas.create_oval(x + 43, y + 25, x + 53, y + 35, fill="#BBF1B9", tags=("point", "output"))
            points.append(out)

        else:
            # two inputs
            points.append(self.canvas.create_oval(x + 10, y + 17, x + 20, y + 27, fill="#BBF1B9", tags=("point", "input")))
            points.append(self.canvas.create_oval(x + 10, y + 29, x + 20, y + 39, fill="#BBF1B9", tags=("point", "input")))
            out = self.canvas.create_oval(x + 44, y + 23, x + 54, y + 33, fill="#F1B9B9", tags=("point", "output"))
            points.append(out)

        self.gates.append(gate)
        self.gate_data[gate] = {"points": points, "wires": []}
        print(self.gate_data[gate])

        print("Gate:", name)
        for p in points:
            print("  → Point tags:", self.canvas.gettags(p))

        return gate

    @staticmethod
    def start_drag_sidebar(name):
        def start(event, self=None):
            self.current_drag_image = self.canvas.create_image(event.x_root, event.y_root, image=self.gate_photos[name])
            self.current_drag_name = name

        return start

    @staticmethod
    def do_drag_sidebar(event, self=None):
        if self.current_drag_image:
            x = event.x_root - self.canvas.winfo_rootx()
            y = event.y_root - self.canvas.winfo_rooty()
            self.canvas.coords(self.current_drag_image, x, y)

    @staticmethod
    def stop_drag_sidebar(event, self=None):
        if self.current_drag_image:
            x = event.x_root - self.canvas.winfo_rootx()
            y = event.y_root - self.canvas.winfo_rooty()
            self.canvas.delete(self.current_drag_image)
            AppFunctions.create_gate(self.current_drag_name, x, y, self)
            self.current_drag_image = None
            self.current_drag_name = None

    @staticmethod
    def save_circuit(self=None):
        gate_info = []
        for gate in self.gates:
            tags = self.canvas.gettags(gate)
            coords = self.canvas.coords(gate)
            gate_info.append({
                'type': tags[1],
                'x': coords[0],
                'y': coords[1]
            })

        wire_info = []
        for wire_id, from_point, to_point in self.wires:
            from_coords = self.canvas.coords(from_point)
            to_coords = self.canvas.coords(to_point)
            wire_info.append({
                'from': from_coords,
                'to': to_coords
            })

        save_path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json")])
        if save_path:
            with open(save_path, "w") as f:
                json.dump({'gates': gate_info, 'wires': wire_info}, f, indent=2)

    @staticmethod
    def load_circuit(self=None):
        try:
            load_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
            if not load_path:
                return

            with open(load_path, "r") as f:
                saved_data = json.load(f)

            for g in list(self.gates):
                AppFunctions.delete_gate(g, self)
            self.wires.clear()

            point_map = {}
            for item in saved_data['gates']:
                gate = AppFunctions.create_gate(item['type'], item['x'], item['y'], self)
                for i, p in enumerate(self.gate_data[gate]['points']):
                    coord = self.canvas.coords(p)
                    point_map[tuple(round(v, 1) for v in coord)] = p

            for wire in saved_data['wires']:
                from_coords = tuple(round(v, 1) for v in wire['from'])
                to_coords = tuple(round(v, 1) for v in wire['to'])
                from_point = point_map.get(from_coords)
                to_point = point_map.get(to_coords)
                if from_point and to_point:
                    x1 = (from_coords[0] + from_coords[2]) / 2
                    y1 = (from_coords[1] + from_coords[3]) / 2
                    x2 = (to_coords[0] + to_coords[2]) / 2
                    y2 = (to_coords[1] + to_coords[3]) / 2
                    line_id = self.canvas.create_line(x1, y1, x2, y2, fill="black", width=2)
                    self.wires.append((line_id, from_point, to_point))
                    for gate_id, data in self.gate_data.items():
                        if from_point in data['points'] or to_point in data['points']:
                            data['wires'].append(line_id)
        except Exception as e:
            print("خطأ أثناء التحميل:", e)

    @staticmethod
    def toggle_delete(self=None):
        self.delete_mode = not self.delete_mode
        self.delete_show.config(relief="sunken" if self.delete_mode else "raised", image=self.disposal)
        self.info.config(text='Delete mode')
        if not self.delete_mode:
            self.delete_show.config(border=False, highlightcolor='black', highlightthickness=0, highlightbackground='white',
                               borderwidth=0, image=self.delete)
            self.info.config(text='')

    @staticmethod
    def delete_gate(gate, self=None):
        for wire in self.gate_data[gate]['wires']:
            for w in self.wires[:]:
                if w[0] == wire:
                    self.canvas.delete(w[0])
                    self.wires.remove(w)
        for p in self.gate_data[gate]['points']:
            self.canvas.delete(p)
        self.canvas.delete(gate)
        self.gates.remove(gate)
        del self.gate_data[gate]

    @staticmethod
    def on_canvas_click(event, self=None):
        clicked_items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        if self.delete_mode:
            for item in clicked_items:
                if item in self.gate_data:
                    AppFunctions.delete_gate(item, self)
                    return
        clicked_items = self.canvas.find_overlapping(event.x, event.y, event.x, event.y)
        clicked = next((item for item in clicked_items if "point" in self.canvas.gettags(item)), None)
        if clicked:
            coords = self.canvas.coords(clicked)
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            if not self.start_point:
                self.start_point = clicked
                self.current_line = self.canvas.create_line(cx, cy, event.x, event.y, fill="black", width=2, tags="wire_preview")
            else:
                if clicked != self.start_point:
                    self.canvas.coords(self.current_line, *self.canvas.coords(self.current_line)[:2], cx, cy)
                    self.wires.append((self.current_line, self.start_point, clicked))
                    for self.gate_id, data in self.gate_data.items():
                        if self.start_point in data["points"] or clicked in data["points"]:
                            data["wires"].append(self.current_line)
                    self.start_point = None
                    self.current_line = None
        else:
            for item in clicked_items:
                if "gate" in self.canvas.gettags(item):
                    self.drag_data["item"] = item
                    self.drag_data["x"] = event.x
                    self.drag_data["y"] = event.y
                    break

    @staticmethod
    def on_mouse_move(event, self=None):
        if self.current_line and self.start_point:
            coords = self.canvas.coords(self.start_point)
            cx = (coords[0] + coords[2]) / 2
            cy = (coords[1] + coords[3]) / 2
            self.canvas.coords(self.current_line, cx, cy, event.x, event.y)

    @staticmethod
    def on_hover_motion(event, self=None):
        AppFunctions.on_mouse_move(event, self)
        hovered = next((item for item in self.canvas.find_overlapping(event.x, event.y, event.x, event.y) if
                        "point" in self.canvas.gettags(item)), None)
        if hovered != self.hover_point:
            if self.hover_point: AppFunctions.reset_point_style(self.hover_point, self)
            if hovered: AppFunctions.highlight_point(hovered, self)
            self.hover_point = hovered

    @staticmethod
    def highlight_point(point_id, self=None):
        coords = self.canvas.coords(point_id)
        cx, cy = AppFunctions.center_of(coords)
        self.canvas.coords(point_id, cx - 7, cy - 7, cx + 7, cy + 7)
        self.canvas.itemconfig(point_id, outline="#00087B", width=2)

    @staticmethod
    def reset_point_style(point_id, self=None):
        coords = self.canvas.coords(point_id)
        cx, cy = AppFunctions.center_of(coords)
        self.canvas.coords(point_id, cx - 5, cy - 5, cx + 5, cy + 5)
        self.canvas.itemconfig(point_id, outline="black", width=1)

    @staticmethod
    def center_of(coords):
        try:
            return (coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2
        except Exception as e:
            messagebox.showerror("Error", f"Something wrong please save your project and restert the program: {e}")


    @staticmethod
    def on_canvas_drag(event, self=None):
        if self.current_line and self.start_point:
            AppFunctions.on_mouse_move(event, self)
        elif self.drag_data["item"]:
            dx = event.x - self.drag_data["x"]
            dy = event.y - self.drag_data["y"]
            self.drag_data["x"] = event.x
            self.drag_data["y"] = event.y
            self.canvas.move(self.drag_data["item"], dx, dy)
            gate_id = self.drag_data["item"]
            for point in self.gate_data[gate_id]["points"]:
                self.canvas.move(point, dx, dy)
            for wire in self.gate_data[gate_id]["wires"]:
                AppFunctions.update_wire_coords(wire, self)

    @staticmethod
    def update_wire_coords(wire_id, self=None):
        for line_id, p1, p2 in self.wires:
            if wire_id == line_id:
                x1, y1 = AppFunctions.center_of(self.canvas.coords(p1))
                x2, y2 = AppFunctions.center_of(self.canvas.coords(p2))
                self.canvas.coords(line_id, x1, y1, x2, y2)

    @staticmethod
    def on_canvas_release(event, self=None):
        self.drag_data["item"] = None



root = AppDesign()

if __name__ == '__main__':
    root.canvas.bind("<Button-1>", lambda event: AppFunctions.on_canvas_click(event, root))
    root.canvas.bind("<B1-Motion>", lambda event: AppFunctions.on_canvas_drag(event, root))
    root.canvas.bind("<ButtonRelease-1>", lambda event: AppFunctions.on_canvas_release(event, root))
    root.canvas.bind("<Motion>", lambda event: AppFunctions.on_hover_motion(event, root))
    root.canvas.bind("<Button-3>", lambda event: AppFunctions.on_canvas_click(event, root))

    # Create sidebar buttons for each gate
    for gate_name in root.gate_photos:
        img = root.gate_photos[gate_name]
        lbl = Label(root.sidebar, image=img, bg="white")
        lbl.pack(pady=3)
        lbl.bind("<Button-1>", lambda event, name=gate_name, s=root: AppFunctions.start_drag_sidebar(name)(event, s))
        lbl.bind("<B1-Motion>", lambda event, s=root: AppFunctions.do_drag_sidebar(event, s))
        lbl.bind("<ButtonRelease-1>", lambda event, s=root: AppFunctions.stop_drag_sidebar(event, s))

    threading.Thread(target=AppFunctions.show_loading_window, args=(root,), daemon=True).start()

    root.mainloop()






