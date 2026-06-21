import sys
import re
import os
import gi

gi.require_version("Gtk", "4.0")
from gi.repository import Gtk, Gio

from displays import DisplayManager


class NoctaliaDisplaysWindow(Gtk.ApplicationWindow):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.set_title("Noctia Displays - Centro de Control")
        self.set_default_size(380, 420)

        self.dm = DisplayManager()
        self.resoluciones_y_hz = {}

        # Contenedor vertical principal
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_top(18)
        main_box.set_margin_bottom(18)
        main_box.set_margin_start(18)
        main_box.set_margin_end(18)
        self.set_child(main_box)

        # 🖥️ SECCIÓN DEL CANVAS DE POSICIONAMIENTO VISUAL
        lbl_visual = Gtk.Label(label="Distribución Física y Rotación de Pantallas:")
        lbl_visual.set_halign(Gtk.Align.START)
        main_box.append(lbl_visual)

        btn_canvas = Gtk.Button(label="🗺️ Abrir Disposición Visual (Arrastrar Monitores / Rotar)")
        btn_canvas.connect("clicked", self.on_abrir_canvas_clicked)
        main_box.append(btn_canvas)

        separator1 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.append(separator1)

        # ⚙️ SECCIÓN DE PARÁMETROS INTERNOS (TUS LISTAS LIMPIAS)
        lbl_monitor = Gtk.Label(label="Monitor a ajustar:")
        lbl_monitor.set_halign(Gtk.Align.START)
        main_box.append(lbl_monitor)

        self.combo_monitors = Gtk.DropDown.new_from_strings([])
        main_box.append(self.combo_monitors)

        # RESOLUCIÓN
        lbl_res = Gtk.Label(label="Resolución:")
        lbl_res.set_halign(Gtk.Align.START)
        main_box.append(lbl_res)

        self.combo_res = Gtk.DropDown.new_from_strings([])
        main_box.append(self.combo_res)

        # FRECUENCIA ORDENADA DE MAYOR A MENOR
        lbl_hz = Gtk.Label(label="Frecuencia (Tasa de refresco):")
        lbl_hz.set_halign(Gtk.Align.START)
        main_box.append(lbl_hz)

        self.combo_hz = Gtk.DropDown.new_from_strings([])
        main_box.append(self.combo_hz)

        # BOTÓN APLICAR CAMBIOS DE FRECUENCIA
        btn_aplicar = Gtk.Button(label="💾 Aplicar Resolución y Hz")
        btn_aplicar.add_css_class("suggested-action")
        btn_aplicar.connect("clicked", self.on_btn_aplicar_clicked)
        main_box.append(btn_aplicar)

        # CONTROLADORES AMD GRÁFICOS
        separator2 = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        separator2.set_margin_top(6)
        main_box.append(separator2)

        lbl_amd = Gtk.Label(label="Controlador de Gráficos AMD (Kernel Line):")
        lbl_amd.set_halign(Gtk.Align.START)
        main_box.append(lbl_amd)

        btn_amd = Gtk.Button(label="⚙️ Abrir Panel Avanzado de GPU (LACT)")
        btn_amd.connect("clicked", self.on_abrir_lact_clicked)
        main_box.append(btn_amd)

        # CONEXIÓN DE EVENTOS
        self.combo_monitors.connect("notify::selected-item", self.on_monitor_changed)
        self.combo_res.connect("notify::selected-item", self.on_res_changed)

        self.bloquear_senales = False
        self.load_initial_monitors()

    def load_initial_monitors(self):
        monitors = self.dm.get_monitors()
        strings = [m["name"] for m in monitors]
        model = Gtk.StringList.new(strings)
        self.combo_monitors.set_model(model)

        if monitors:
            self.combo_monitors.set_selected(0)

    def on_monitor_changed(self, dropdown, pspec):
        selected_item = dropdown.get_selected_item()
        if not selected_item: return
        monitor_name = selected_item.get_string()

        self.bloquear_senales = True
        modes = self.dm.get_monitor_modes(monitor_name)

        self.resoluciones_y_hz.clear()
        for mode in modes:
            match = re.match(r"(\d+x\d+)@([\d.]+)", mode)
            if match:
                res = match.group(1)  
                hz = int(float(match.group(2)))  

                if res not in self.resoluciones_y_hz:
                    self.resoluciones_y_hz[res] = []
                if hz not in self.resoluciones_y_hz[res]:
                    self.resoluciones_y_hz[res].append(hz)

        lista_resoluciones = list(self.resoluciones_y_hz.keys())
        model_res = Gtk.StringList.new(lista_resoluciones)
        self.combo_res.set_model(model_res)

        self.bloquear_senales = False

        if lista_resoluciones:
            self.combo_res.set_selected(0)
            self.actualizar_lista_hz(lista_resoluciones[0])

    def on_res_changed(self, dropdown, pspec):
        if self.bloquear_senales: return
        selected_res_item = dropdown.get_selected_item()
        if selected_res_item:
            self.actualizar_lista_hz(selected_res_item.get_string())

    def actualizar_lista_hz(self, res_name):
        self.bloquear_senales = True
        hz_numeros = self.resoluciones_y_hz.get(res_name, [])
        hz_numeros.sort(reverse=True) # Mayor a menor matemático
        
        hz_amigables = [f"{val} Hz (Recomendado)" if i == 0 else f"{val} Hz" for i, val in enumerate(hz_numeros)]
        
        model_hz = Gtk.StringList.new(hz_amigables)
        self.combo_hz.set_model(model_hz)
        self.bloquear_senales = False
        
        if hz_amigables:
            self.combo_hz.set_selected(0)

    def on_btn_aplicar_clicked(self, button):
        """Dispara de forma segura el cambio de Hz sin alterar posiciones"""
        monitor_item = self.combo_monitors.get_selected_item()
        res_item = self.combo_res.get_selected_item()
        hz_item = self.combo_hz.get_selected_item()

        if not monitor_item or not res_item or not hz_item: return

        monitor_name = monitor_item.get_string()
        res_string = res_item.get_string()  
        hz_string = hz_item.get_string()  

        match_res = re.match(r"(\d+)x(\d+)", res_string)
        match_hz = re.match(r"(\d+)", hz_string)

        if match_res and match_hz:
            width = int(match_res.group(1))
            height = int(match_res.group(2))
            hz = int(match_hz.group(1))

            self.dm.set_monitor_resolucion_hz(output=monitor_name, width=width, height=height, hz=hz)

    def on_abrir_canvas_clicked(self, button):
        """Levanta de forma nativa e integrada el gestor de arrastre visual del sistema"""
        os.system("nwg-displays &")

    def on_abrir_lact_clicked(self, button):
        os.system("lact-gui & || /usr/bin/lact-gui &")


class NoctaliaDisplaysApp(Gtk.Application):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, application_id="io.cachyos.noctalia.displays", flags=Gio.ApplicationFlags.FLAGS_NONE, **kwargs)

    def do_activate(self):
        window = NoctaliaDisplaysWindow(application=self)
        window.present()


if __name__ == "__main__":
    app = NoctaliaDisplaysApp()
    sys.exit(app.run(sys.argv))
