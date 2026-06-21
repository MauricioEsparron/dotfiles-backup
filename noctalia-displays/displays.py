import subprocess
import json
import sys
import os
import re

class DisplayManager:
    """
    Backend unificado que lee el hardware de Hyprland, extrae el layout 
    visual de nwg-displays y genera comandos de Lua en tiempo real.
    """

    def get_monitors(self):
        try:
            result = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True)
            monitors_json = json.loads(result.stdout)
            return [{"name": m["name"]} for m in monitors_json]
        except Exception as e:
            print(f"Error al obtener monitores: {e}", file=sys.stderr)
            return []

    def get_monitor_modes(self, monitor_name):
        try:
            result = subprocess.run(["hyprctl", "monitors", "-j"], capture_output=True, text=True, check=True)
            monitors_json = json.loads(result.stdout)
            for m in monitors_json:
                if m["name"] == monitor_name:
                    return m.get("availableModes", [])
            return []
        except Exception as e:
            return []

    def obtener_posicion_guardada_nwg(self, monitor_name):
        """
        Lee el archivo generado por el Canvas visual y extrae la posición XxY y la rotación.
        Si no encuentra el archivo o el monitor, devuelve valores por defecto seguros.
        """
        ruta_nwg = os.path.expanduser("~/.config/hypr/monitors.conf")
        posicion_defecto = "0x0"
        transform_defecto = "0"
        
        if not os.path.exists(ruta_nwg):
            return posicion_defecto, transform_defecto

        try:
            with open(ruta_nwg, "r") as f:
                for line in f:
                    # Busca líneas tipo: monitor=HDMI-A-1,1920x1080@240.0,0x0,1.0
                    # O con transformaciones al final
                    if line.strip().startswith("monitor") and monitor_name in line:
                        partes = line.split(",")
                        if len(partes) >= 4:
                            posicion_defecto = partes[2].strip() # Extrae "0x0" o "1920x0"
                        return posicion_defecto, transform_defecto
        except Exception as e:
            print(f"Error leyendo posiciones de nwg: {e}", file=sys.stderr)
            
        return posicion_defecto, transform_defecto

    def set_monitor_resolucion_hz(self, output, width, height, hz):
        """
        Combina tus Hz seleccionados con la posición del Canvas visual 
        e inyecta todo en el intérprete de Lua.
        """
        # 1. Recuperar la posición exacta del Canvas de la derecha
        posicion, transform = self.obtener_posicion_guardada_nwg(output)
        
        # 2. Buscar si hay otro monitor para no perder su posición actual
        monitores = self.get_monitors()
        otro_cmd_lua = ""
        for m in monitores:
            if m["name"] != output:
                o_name = m["name"]
                o_pos, o_trans = self.obtener_posicion_guardada_nwg(o_name)
                # Dejamos al otro monitor en modo automático para que no se apague, pero en su coordenada del Canvas
                otro_cmd_lua = f' hl.monitor({{ output = "{o_name}", mode = "auto", position = "{o_pos}", scale = 1 }})'
                break

        # 3. Construir la cadena de comandos Lua unificada
        lua_command = f'hl.monitor({{ output = "{output}", mode = "{width}x{height}@{hz}", position = "{posicion}", scale = 1 }})'
        lua_command += otro_cmd_lua
        
        try:
            # Sincronización forzada directa al motor de Hyprland
            subprocess.run(["hyprctl", "eval", lua_command], check=True)
            print(f"\n[SISTEMA OS] Cambios aplicados con éxito:")
            print(f"🖥️ Monitor: {output} -> {width}x{height}@{hz}Hz en posición [{posicion}]")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error al enviar datos a Hyprland: {e}", file=sys.stderr)
            return False
