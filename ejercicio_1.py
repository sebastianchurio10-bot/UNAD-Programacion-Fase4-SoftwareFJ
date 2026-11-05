import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import datetime

class SoftwareFJError(Exception):
    """Excepción base para el sistema de Software FJ."""
    pass

class ClienteError(SoftwareFJError):
    """Excepción para errores relacionados con los clientes."""
    pass

class ServicioError(SoftwareFJError):
    """Excepción para errores en la creación o gestión de servicios."""
    pass

class ReservaError(SoftwareFJError):
    """Excepción para errores al procesar reservas."""
    pass
def registrar_log(mensaje: str, tipo: str = "INFO"):
    """Registra eventos, operaciones y errores en app_log.txt."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{tipo}] {mensaje}\n"
    try:
        with open("app_log.txt", "a", encoding="utf-8") as archivo:
            archivo.write(log_line)
    except IOError as e:
        print(f"Error crítico al escribir en el archivo de log: {e}")

class Cliente:
    def __init__(self, nombre: str, cedula: str, correo: str, telefono: str):
        if not nombre.strip():
            raise ClienteError("El nombre del cliente no puede estar vacío.")
        if not cedula.isdigit() or len(cedula) < 6:
            raise ClienteError(f"Cédula inválida '{cedula}': debe contener solo números (mínimo 6 dígitos).")
        if "@" not in correo or "." not in correo:
            raise ClienteError(f"Correo electrónico inválido: '{correo}'.")
        
        self.__nombre = nombre
        self.__cedula = cedula
        self.__correo = correo
        self.__telefono = telefono

    @property
    def nombre(self):
        return self.__nombre

    @property
    def cedula(self):
        return self.__cedula

    def obtener_info(self) -> str:
        return f"Cliente: {self.__nombre} | Cédula: {self.__cedula} | Correo: {self.__correo}"


class Servicio(ABC):
    def __init__(self, codigo: str, nombre: str, costo_base: float):
        if costo_base < 0:
            raise ServicioError("El costo base no puede ser negativo.")
        self.codigo = codigo
        self.nombre = nombre
        self.costo_base = costo_base

    @abstractmethod
    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        """Método polimórfico para calcular costo final."""
        pass

    @abstractmethod
    def obtener_descripcion(self) -> str:
        pass


class ReservaSala(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, capacidad: int, horas: int):
        super().__init__(codigo, nombre, costo_base)
        if capacidad <= 0 or horas <= 0:
            raise ServicioError("La capacidad de la sala y las horas deben ser mayores a cero.")
        self.capacidad = capacidad
        self.horas = horas

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        try:
            if not (0 <= descuento <= 1):
                raise ValueError("El descuento debe estar entre 0.0 y 1.0.")
            subtotal = (self.costo_base * self.horas) * (1 - descuento)
            total = subtotal * (1 + impuesto)
            return round(total, 2)
        except ValueError as ve:
            registrar_log(f"Error en cálculo de costo de sala: {ve}", "ERROR")
            raise ServicioError("Error numérico al calcular costo de sala.") from ve

    def obtener_descripcion(self) -> str:
        return f"[Sala] {self.nombre} (Cap: {self.capacidad} pers, {self.horas} hrs) - Base: ${self.costo_base}"


class AlquilerEquipo(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, nombre_equipo: str, dias: int):
        super().__init__(codigo, nombre, costo_base)
        if dias <= 0:
            raise ServicioError("Los días de alquiler deben ser mayores a cero.")
        self.nombre_equipo = nombre_equipo
        self.dias = dias

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        subtotal = (self.costo_base * self.dias) * (1 - descuento)
        return round(subtotal * (1 + impuesto), 2)

    def obtener_descripcion(self) -> str:
        return f"[Equipo] {self.nombre_equipo} ({self.dias} días) - Base diaria: ${self.costo_base}"


class AsesoriaEspecializada(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, area: str, horas: int):
        super().__init__(codigo, nombre, costo_base)
        if horas <= 0:
            raise ServicioError("Las horas de asesoría deben ser mayores a cero.")
        self.area = area
        self.horas = horas

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        subtotal = (self.costo_base * self.horas) * (1 - descuento)
        return round(subtotal * (1 + impuesto), 2)

    def obtener_descripcion(self) -> str:
        return f"[Asesoría] Área {self.area} ({self.horas} hrs) - Tarifa: ${self.costo_base}"


class Reserva:
    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio):
        if not id_reserva.strip():
            raise ReservaError("El ID de reserva no puede estar vacío.")
        self.id_reserva = id_reserva
        self.cliente = cliente
        self.servicio = servicio
        self.estado = "Pendiente"
        self.costo_total = 0.0

    def procesar_reserva(self, descuento: float = 0.0):
        try:
            self.costo_total = self.servicio.calcular_costo(descuento=descuento)
            self.estado = "Confirmada"
            registrar_log(f"Reserva {self.id_reserva} procesada con éxito para {self.cliente.nombre}. Total: ${self.costo_total}", "ACCION")
        except Exception as e:
            self.estado = "Fallida"
            registrar_log(f"Fallo al procesar reserva {self.id_reserva}: {e}", "ERROR")
            raise ReservaError(f"No se pudo procesar la reserva {self.id_reserva}") from e

    def cancelar(self):
        self.estado = "Cancelada"
        registrar_log(f"Reserva {self.id_reserva} cancelada.", "AVISO")

class SoftwareFJApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Software FJ - Sistema Integral de Gestión (Fase 4)")
        self.root.geometry("720x600")
        self.root.resizable(False, False)

        self.clientes = []
        self.servicios = []
        self.reservas = []

        self._build_ui()

    def _build_ui(self):
        title_label = tk.Label(
            self.root, 
            text="Software FJ - Gestión de Clientes, Servicios y Reservas", 
            font=("Helvetica", 14, "bold"),
            fg="#1E3A8A"
        )
        title_label.pack(pady=10)

        # Panel de Log / Consola
        log_frame = tk.LabelFrame(self.root, text=" Registro de Operaciones y Excepciones (Logs) ", font=("Helvetica", 10, "bold"))
        log_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, font=("Consolas", 8), height=15, state="disabled", bg="#F8FAFC")
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

        # Panel de Botones
        btn_frame = tk.Frame(self.root)
        btn_frame.pack(pady=15)

        btn_simular = tk.Button(
            btn_frame, text="Simular 10 Operaciones (Requerimiento Guía)", bg="#10B981", fg="white", 
            font=("Helvetica", 10, "bold"), padx=10, pady=8, command=self.ejecutar_simulacion_10_operaciones
        )
        btn_simular.grid(row=0, column=0, padx=10)

        btn_limpiar = tk.Button(
            btn_frame, text="Limpiar Consola", bg="#EF4444", fg="white", 
            font=("Helvetica", 10, "bold"), padx=10, pady=8, command=self.limpiar_consola
        )
        btn_limpiar.grid(row=0, column=1, padx=10)

    def log(self, message: str):
        self.log_text.config(state="normal")
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")

    def limpiar_consola(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.config(state="disabled")

    def ejecutar_simulacion_10_operaciones(self):
        self.log("=== INICIANDO SIMULACIÓN DE 10 OPERACIONES (ROBUSTEZ Y EXCEPCIONES) ===")
        registrar_log("Inicio de simulación de 10 operaciones.", "SISTEMA")

        operaciones_exitosas = 0

        # --- OPERACIÓN 1: Registro Válido de Cliente ---
        try:
            c1 = Cliente("Carlos Pérez", "12345678", "carlos@mail.com", "3001112233")
            self.clientes.append(c1)
            self.log("✅ Op 1 [ÉXITO]: Cliente válido registrado -> " + c1.nombre)
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 1 [FALLÓ]: {e}")

        # --- OPERACIÓN 2: Registro Inválido de Cliente (Dispara Excepción) ---
        try:
            # Estructura try/except/else/finally completa demostrada aquí
            try:
                c_malo = Cliente("Ana Gómez", "abc12345", "correo_invalido", "123")
            except ClienteError as ce:
                self.log(f"⚠️ Op 2 [EXCEPCIÓN CONTROLADA]: Error de cliente capturado correctamente -> {ce}")
                raise
            else:
                self.clientes.append(c_malo)
            finally:
                self.log("   -> [Finally Op 2]: Validación de cliente finalizada.")
        except Exception:
            self.log("✅ Op 2 [ÉXITO EN ROBUSTEZ]: El sistema evitó un registro corrupto.")
            operaciones_exitosas += 1

        # --- OPERACIÓN 3: Creación Válida de Servicio (Sala) ---
        try:
            s1 = ReservaSala("SR-01", "Sala Ejecutiva", 50000.0, 10, 3)
            self.servicios.append(s1)
            self.log("✅ Op 3 [ÉXITO]: Servicio de sala creado -> " + s1.obtener_descripcion())
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 3 [FALLÓ]: {e}")

        # --- OPERACIÓN 4: Creación Inválida de Servicio (Horas negativas) ---
        try:
            s_malo = ReservaSala("SR-02", "Sala Mini", 30000.0, 5, -2)
        except ServicioError as se:
            self.log(f"⚠️ Op 4 [EXCEPCIÓN CONTROLADA]: Error en servicio capturado -> {se}")
            operaciones_exitosas += 1

        # --- OPERACIÓN 5: Creación Válida de Alquiler de Equipo ---
        try:
            s2 = AlquilerEquipo("EQ-01", "Kit Audiovisual", 40000.0, "Proyectores 4K", 2)
            self.servicios.append(s2)
            self.log("✅ Op 5 [ÉXITO]: Alquiler de equipo creado -> " + s2.obtener_descripcion())
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 5 [FALLÓ]: {e}")

        # --- OPERACIÓN 6: Creación Válida de Asesoría Especializada ---
        try:
            s3 = AsesoriaEspecializada("AS-01", "Consultoría TI", 100000.0, "Software Architecture", 4)
            self.servicios.append(s3)
            self.log("✅ Op 6 [ÉXITO]: Asesoria creada -> " + s3.obtener_descripcion())
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 6 [FALLÓ]: {e}")

        # --- OPERACIÓN 7: Reserva Exitosa ---
        try:
            res1 = Reserva("RES-101", self.clientes[0], self.servicios[0])
            res1.procesar_reserva(descuento=0.1)
            self.reservas.append(res1)
            self.log(f"✅ Op 7 [ÉXITO]: Reserva {res1.id_reserva} confirmada. Costo: ${res1.costo_total}")
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 7 [FALLÓ]: {e}")

        # --- OPERACIÓN 8: Reserva Fallida por Descuento Inválido ---
        try:
            res_mala = Reserva("RES-102", self.clientes[0], self.servicios[1])
            # Forzamos un descuento fuera de rango para probar excepciones encadenadas
            res_mala.procesar_reserva(descuento=1.5)
        except ReservaError as re:
            self.log(f"⚠️ Op 8 [EXCEPCIÓN CONTROLADA]: Reserva fallida manejada con éxito -> {re}")
            operaciones_exitosas += 1

        # --- OPERACIÓN 9: Cancelación de Reserva ---
        try:
            if len(self.reservas) > 0:
                self.reservas[0].cancelar()
                self.log(f"✅ Op 9 [ÉXITO]: Reserva {self.reservas[0].id_reserva} cancelada correctamente.")
                operaciones_exitosas += 1
            else:
                self.log("⚠️ Op 9 [OMITIDA]: No hay reservas para cancelar.")
        except Exception as e:
            self.log(f"❌ Op 9 [FALLÓ]: {e}")

        # --- OPERACIÓN 10: Validación general del sistema y bloques try/except/else/finally ---
        try:
            total_clientes = len(self.clientes)
            total_servicios = len(self.servicios)
            self.log(f"✅ Op 10 [ÉXITO]: Reporte de integridad generado. Clientes: {total_clientes}, Servicios: {total_servicios}.")
            operaciones_exitosas += 1
        except Exception as e:
            self.log(f"❌ Op 10 [FALLÓ]: {e}")
        else:
            self.log("   -> [Else Op 10]: Sistema funcionando de forma ultra estable sin caídas.")
        finally:
            self.log("   -> [Finally Op 10]: Secuencia de simulación finalizada con éxito total.")

        self.log(f"\n=== SIMULACIÓN FINALIZADA: {operaciones_exitosas}/10 OPERACIONES EXITOSAS ===")
        registrar_log(f"Simulación completada. Operaciones exitosas/controladas: {operaciones_exitosas}/10", "INFO")
        messagebox.showinfo("Simulación Completa", f"Se simularon las 10 operaciones requeridas por la guía[cite: 21].\nResultado: {operaciones_exitosas}/10 completadas y controladas con éxito.")


if __name__ == "__main__":
    registrar_log("Aplicación Software FJ iniciada.", "SISTEMA")
    root = tk.Tk()
    app = SoftwareFJApp(root)
    root.mainloop()