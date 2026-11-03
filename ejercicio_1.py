import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import datetime

# ==========================================
# EXCEPCIONES PERSONALIZADAS Y ENCADENAMIENTO
# ==========================================
class VehiculoError(Exception):
    """Excepción base para errores del sistema de vehículos."""
    pass

class BateriaAgotadaError(VehiculoError):
    """Excepción lanzada cuando el auto eléctrico se queda sin batería."""
    pass

class CargaExcedidaError(VehiculoError):
    """Excepción lanzada cuando la carga supera el límite del camión."""
    pass
def registrar_log(mensaje: str, tipo: str = "INFO"):
    """Registra eventos y errores en un archivo de texto local (app_log.txt)."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{tipo}] {mensaje}\n"
    try:
        with open("app_log.txt", "a", encoding="utf-8") as archivo:
            archivo.write(log_line)
    except IOError as e:
        print(f"Error crítico al escribir en el archivo de log: {e}")

class Vehiculo(ABC):
    def __init__(self, marca: str, modelo: str, velocidad_actual: float):
        if velocidad_actual < 0:
            raise ValueError("La velocidad inicial no puede ser negativa.")
        self.marca = marca
        self.modelo = modelo
        self.velocidad_actual = velocidad_actual

    def acelerar(self, turbo: float = 0.0, terreno: str = "normal") -> str:
        try:
            if turbo < 0:
                raise ValueError("El valor del turbo no puede ser negativo.")
            
            incremento = 10.0 + turbo
            terreno_lower = terreno.lower()
            
            if terreno_lower == "rocky":
                incremento *= 0.5
            elif terreno_lower == "track":
                incremento *= 1.5
            elif terreno_lower not in ["normal", "rocky", "track"]:
                raise ValueError(f"Terreno '{terreno}' no reconocido.")

            self.velocidad_actual += incremento
            resultado = f"[{self.marca} {self.modelo}] Acelerando en terreno '{terreno}'. Velocidad: {self.velocidad_actual:.1f} km/h"
            registrar_log(resultado, "ACCION")
            return resultado

        except ValueError as ve:
            error_msg = f"Falla de validación en {self.marca} {self.modelo}"
            registrar_log(f"{error_msg}: {ve}", "ERROR")
            raise VehiculoError(error_msg) from ve

    @abstractmethod
    def detener(self) -> str:
        pass

    def obtener_informacion(self) -> str:
        return f"[{self.__class__.__name__}] {self.marca} {self.modelo} | Velocidad: {self.velocidad_actual:.1f} km/h"


class AutoElectrico(Vehiculo):
    def __init__(self, marca: str, modelo: str, velocidad_actual: float, nivel_bateria: int):
        super().__init__(marca, modelo, velocidad_actual)
        if not (0 <= nivel_bateria <= 100):
            raise ValueError("El nivel de batería debe estar entre 0% y 100%.")
        self.nivel_bateria = nivel_bateria

    def acelerar(self, turbo: float = 0.0, terreno: str = "normal") -> str:
        if self.nivel_bateria <= 0:
            msg = f"Batería agotada en {self.marca} {self.modelo}."
            registrar_log(msg, "ADVERTENCIA")
            raise BateriaAgotadaError(msg)
        
        base_msg = super().acelerar(turbo + 5.0, terreno)
        self.nivel_bateria = max(0, self.nivel_bateria - 5)
        return f"⚡ [Modo Eléctrico] {base_msg} | Batería: {self.nivel_bateria}%"

    def detener(self) -> str:
        self.velocidad_actual = 0.0
        msg = f"🔋 {self.marca} {self.modelo}: Freno regenerativo aplicado. Detenido."
        registrar_log(msg, "ACCION")
        return msg


class Moto(Vehiculo):
    def __init__(self, marca: str, modelo: str, velocidad_actual: float, cilindrada: int):
        super().__init__(marca, modelo, velocidad_actual)
        if cilindrada <= 0:
            raise ValueError("La cilindrada debe ser mayor a 0 cc.")
        self.cilindrada = cilindrada

    def acelerar(self, turbo: float = 0.0, terreno: str = "normal") -> str:
        base_msg = super().acelerar(turbo + 15.0, terreno)
        return f"🏍️ [{self.cilindrada}cc] {base_msg} | ¡Aceleración rápida!"

    def detener(self) -> str:
        self.velocidad_actual = 0.0
        msg = f"🛑 {self.marca} {self.modelo}: Frenado de disco controlado. Detenido."
        registrar_log(msg, "ACCION")
        return msg


class Camion(Vehiculo):
    def __init__(self, marca: str, modelo: str, velocidad_actual: float, capacidad_carga_ton: float):
        super().__init__(marca, modelo, velocidad_actual)
        if capacidad_carga_ton > 40:
            raise CargaExcedidaError(f"Carga de {capacidad_carga_ton} T excede el límite máximo (40 T).")
        self.capacidad_carga_ton = capacidad_carga_ton

    def acelerar(self, turbo: float = 0.0, terreno: str = "normal") -> str:
        base_msg = super().acelerar(max(0.0, turbo - 5.0), terreno)
        return f"🚛 [{self.capacidad_carga_ton} T Carga] {base_msg} | Carga pesada en marcha."

    def detener(self) -> str:
        self.velocidad_actual = 0.0
        msg = f"🛑 {self.marca} {self.modelo}: Frenos neumáticos activados. Detenido."
        registrar_log(msg, "ACCION")
        return msg

class SmartVehiclesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gestión de Vehículos Inteligentes - UNAD (Fase 4)")
        self.root.geometry("680x560")
        self.root.resizable(False, False)

        self.flota = []
        self._inicializar_flota()
        self._build_ui()
        self.update_fleet_status()

    def _inicializar_flota(self):
        try:
            self.flota = [
                AutoElectrico("Tesla", "Model S", 0.0, 100),
                Moto("Yamaha", "MT-09", 0.0, 850),
                Camion("Volvo", "FH16", 0.0, 24.5)
            ]
        except (ValueError, VehiculoError) as e:
            registrar_log(f"Error crítico al iniciar flota: {e}", "CRITICO")
            messagebox.showerror("Error de Configuración", f"No se pudo iniciar la flota: {e}")
        else:
            registrar_log("Flota inicializada exitosamente sin errores.", "INFO")
        finally:
            print("Bloque de inicialización de flota ejecutado (Finally).")

    def _build_ui(self):
        title_label = tk.Label(
            self.root, 
            text="Panel de Control de Flota Inteligente (Fase 4)", 
            font=("Helvetica", 15, "bold"),
            fg="#1E3A8A"
        )
        title_label.pack(pady=10)

        list_frame = tk.LabelFrame(self.root, text=" Estado de la Flota ", font=("Helvetica", 10, "bold"))
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.fleet_listbox = tk.Listbox(list_frame, font=("Consolas", 9), height=5)
        self.fleet_listbox.pack(padx=10, pady=10, fill="both", expand=True)

        log_frame = tk.LabelFrame(self.root, text=" Registro de Ejecución y Errores (Logs) ", font=("Helvetica", 10, "bold"))
        log_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, font=("Consolas", 8), height=8, state="disabled", bg="#F8FAFC")
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        btn_accelerate = tk.Button(
            btn_frame, text="Acelerar Flota", bg="#10B981", fg="white", 
            font=("Helvetica", 9, "bold"), padx=10, pady=5, command=self.accelerate_all
        )
        btn_accelerate.grid(row=0, column=0, padx=5)

        btn_stop = tk.Button(
            btn_frame, text="Detener Flota", bg="#EF4444", fg="white", 
            font=("Helvetica", 9, "bold"), padx=10, pady=5, command=self.stop_all
        )
        btn_stop.grid(row=0, column=1, padx=5)

        btn_refresh = tk.Button(
            btn_frame, text="Actualizar Estado", bg="#3B82F6", fg="white", 
            font=("Helvetica", 9, "bold"), padx=10, pady=5, command=self.update_fleet_status
        )
        btn_refresh.grid(row=0, column=2, padx=5)

    def log(self, message: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def update_fleet_status(self):
        self.fleet_listbox.delete(0, tk.END)
        for idx, veh in enumerate(self.flota):
            self.fleet_listbox.insert(tk.END, f"{idx + 1}: {veh.obtener_informacion()}")

    def accelerate_all(self):
        self.log("--- Ejecutando acelerar() en la flota ---")
        for veh in self.flota:
            try:
                resultado = veh.acelerar(turbo=10.0, terreno="track")
            except BateriaAgotadaError as bae:
                self.log(f"⚠️ {bae}")
                messagebox.showwarning("Batería Agotada", str(bae))
            except VehiculoError as ve:
                self.log(f"❌ {ve}")
            except Exception as ex:
                self.log(f"🔥 Error inesperado: {ex}")
                registrar_log(f"Error inesperado en UI: {ex}", "CRITICO")
            else:
                self.log(f"✅ {resultado}")
            finally:
                print(f"Proceso de aceleración finalizado para {veh.marca}.")
                
        self.update_fleet_status()
        self.log("")

    def stop_all(self):
        self.log("--- Ejecutando detener() en la flota ---")
        for veh in self.flota:
            try:
                res = veh.detener()
            except Exception as e:
                self.log(f"❌ Error al detener: {e}")
            else:
                self.log(res)
            finally:
                pass
        self.update_fleet_status()
        self.log("")


if __name__ == "__main__":
    registrar_log("Aplicación iniciada por el usuario.", "SISTEMA")
    root = tk.Tk()
    app = SmartVehiclesApp(root)
    root.mainloop()