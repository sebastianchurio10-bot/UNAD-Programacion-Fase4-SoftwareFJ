import tkinter as tk
from tkinter import ttk, messagebox
from abc import ABC, abstractmethod
import datetime

# ==========================================
# EXCEPCIONES PERSONALIZADAS Y ENCADENAMIENTO
# ==========================================
class SoftwareFJError(Exception):
    """Excepción base para el sistema de Software FJ."""
    pass

class ClienteError(SoftwareFJError):
    """Excepción para errores relacionados con los clientes."""
    pass

class ServicioError(SoftwareFJError):
    """Excepción para errores en la creación o disponibilidad de servicios."""
    pass

class ReservaError(SoftwareFJError):
    """Excepción para errores al procesar o cancelar reservas."""
    pass


# ==========================================
# SISTEMA DE LOGS (REGISTRO EN ARCHIVO)
# ==========================================
def registrar_log(mensaje: str, tipo: str = "INFO"):
    """Registra eventos, operaciones y errores en app_log.txt."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_line = f"[{timestamp}] [{tipo}] {mensaje}\n"
    try:
        with open("app_log.txt", "a", encoding="utf-8") as archivo:
            archivo.write(log_line)
    except IOError as e:
        print(f"Error crítico al escribir en el archivo de log: {e}")


# ==========================================
# MODELO DE DOMINIO - POO
# ==========================================
class EntidadSistema(ABC):
    """Clase base abstracta para entidades generales del sistema."""
    @abstractmethod
    def obtener_info(self) -> str:
        pass


class Cliente(EntidadSistema):
    def __init__(self, nombre: str, cedula: str, correo: str, telefono: str):
        if not nombre or not nombre.strip():
            raise ClienteError("El nombre del cliente no puede estar vacío.")
        if not cedula or not cedula.isdigit() or len(cedula) < 6:
            raise ClienteError(f"Cédula inválida '{cedula}': debe contener solo números (mínimo 6 dígitos).")
        if not correo or "@" not in correo or "." not in correo:
            raise ClienteError(f"Correo electrónico inválido: '{correo}'.")
        if not telefono or not telefono.isdigit() or len(telefono) < 7:
            raise ClienteError(f"Teléfono inválido '{telefono}': debe contener solo números (mínimo 7 dígitos).")

        self.__nombre = nombre.strip()
        self.__cedula = cedula.strip()
        self.__correo = correo.strip()
        self.__telefono = telefono.strip()

    @property
    def nombre(self) -> str:
        return self.__nombre

    @property
    def cedula(self) -> str:
        return self.__cedula

    @property
    def correo(self) -> str:
        return self.__correo

    @property
    def telefono(self) -> str:
        return self.__telefono

    def obtener_info(self) -> str:
        return f"{self.__nombre} (CC: {self.__cedula}) | Tel: {self.__telefono} | {self.__correo}"


class Servicio(EntidadSistema, ABC):
    def __init__(self, codigo: str, nombre: str, costo_base: float):
        if not codigo or not codigo.strip():
            raise ServicioError("El código del servicio no puede estar vacío.")
        if not nombre or not nombre.strip():
            raise ServicioError("El nombre del servicio no puede estar vacío.")
        if costo_base <= 0:
            raise ServicioError("El costo base debe ser mayor a cero.")

        self.codigo = codigo.strip().upper()
        self.nombre = nombre.strip()
        self.costo_base = float(costo_base)
        self.disponible = True  # Control de disponibilidad

    @abstractmethod
    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        pass

    @abstractmethod
    def obtener_descripcion(self) -> str:
        pass

    def obtener_info(self) -> str:
        estado_disp = "Disponible" if self.disponible else "Ocupado/Reservado"
        return f"[{self.codigo}] {self.obtener_descripcion()} | Estado: {estado_disp}"


    # ------------------------------------------------------------------
    # Método agregado para cubrir la sobrecarga de métodos del Anexo 3.
    # Funciona como calcular_costo, pero admite un parámetro opcional extra
    # (recargo) y devuelve un desglose completo en un diccionario.
    # ------------------------------------------------------------------
    def calcular_costo_detallado(self, descuento: float = 0.0, impuesto: float = 0.19, recargo: float = 0.0) -> dict:
        """Devuelve un diccionario con: subtotal, descuento aplicado, recargo, impuesto y total."""
        try:
            # Validación: el impuesto debe ser una fracción entre 0 (0%) y 1 (100%)
            if not (0.0 <= impuesto <= 1.0):
                raise ValueError("El impuesto debe estar entre 0 y 1.")
            # Validación: el recargo es opcional y no puede ser negativo
            if recargo < 0:
                raise ValueError("El recargo no puede ser negativo.")

            # Cantidad de unidades del servicio: horas (sala/asesoría) o días (equipo); 1 si no define ninguna
            cantidad = getattr(self, "horas", getattr(self, "dias", 1))

            # Subtotal sin descuento: costo base multiplicado por la cantidad de unidades
            subtotal = self.costo_base * cantidad
            # Valor en dinero del descuento aplicado sobre el subtotal
            descuento_aplicado = subtotal * descuento
            # Base sobre la que se calcula el impuesto: subtotal menos descuento, más el recargo
            base_gravable = subtotal - descuento_aplicado + recargo
            # Valor en dinero del impuesto sobre la base gravable
            valor_impuesto = base_gravable * impuesto

            # Desglose completo del costo, redondeado a 2 decimales
            return {
                "subtotal": round(subtotal, 2),
                "descuento_aplicado": round(descuento_aplicado, 2),
                "recargo": round(recargo, 2),
                "impuesto": round(valor_impuesto, 2),
                "total": round(base_gravable + valor_impuesto, 2)
            }
        except ValueError as ve:
            # Encadenamiento de excepciones: "raise from" conserva la causa original del error
            raise ServicioError(f"Parámetros inválidos al calcular el costo detallado: {ve}") from ve

class ReservaSala(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, capacidad: int, horas: int):
        super().__init__(codigo, nombre, costo_base)
        if capacidad <= 0 or horas <= 0:
            raise ServicioError("La capacidad de la sala y las horas deben ser mayores a cero.")
        self.capacidad = capacidad
        self.horas = horas

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        try:
            if not (0.0 <= descuento <= 0.5):
                raise ValueError("El descuento permitido es entre 0% (0.0) y 50% (0.5).")
            subtotal = (self.costo_base * self.horas) * (1 - descuento)
            return round(subtotal * (1 + impuesto), 2)
        except ValueError as ve:
            registrar_log(f"Error en cálculo de sala {self.codigo}: {ve}", "ERROR")
            raise ServicioError(f"Descuento inválido ({descuento}) al calcular costo de sala.") from ve

    def obtener_descripcion(self) -> str:
        return f"Sala '{self.nombre}' (Cap: {self.capacidad} pers, {self.horas} hrs) - Base/h: ${self.costo_base:,.0f}"


class AlquilerEquipo(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, nombre_equipo: str, dias: int):
        super().__init__(codigo, nombre, costo_base)
        if not nombre_equipo or not nombre_equipo.strip():
            raise ServicioError("Debe especificar el equipo a alquilar.")
        if dias <= 0:
            raise ServicioError("Los días de alquiler deben ser mayores a cero.")
        self.nombre_equipo = nombre_equipo.strip()
        self.dias = dias

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        try:
            if not (0.0 <= descuento <= 0.5):
                raise ValueError("El descuento permitido es entre 0% (0.0) y 50% (0.5).")
            subtotal = (self.costo_base * self.dias) * (1 - descuento)
            return round(subtotal * (1 + impuesto), 2)
        except ValueError as ve:
            registrar_log(f"Error en cálculo de equipo {self.codigo}: {ve}", "ERROR")
            raise ServicioError(f"Descuento inválido ({descuento}) al calcular costo de equipo.") from ve

    def obtener_descripcion(self) -> str:
        return f"Equipo '{self.nombre_equipo}' ({self.dias} días) - Base/día: ${self.costo_base:,.0f}"


class AsesoriaEspecializada(Servicio):
    def __init__(self, codigo: str, nombre: str, costo_base: float, area: str, horas: int):
        super().__init__(codigo, nombre, costo_base)
        if not area or not area.strip():
            raise ServicioError("Debe especificar el área de la asesoría.")
        if horas <= 0:
            raise ServicioError("Las horas de asesoría deben ser mayores a cero.")
        self.area = area.strip()
        self.horas = horas

    def calcular_costo(self, descuento: float = 0.0, impuesto: float = 0.19) -> float:
        try:
            if not (0.0 <= descuento <= 0.5):
                raise ValueError("El descuento permitido es entre 0% (0.0) y 50% (0.5).")
            subtotal = (self.costo_base * self.horas) * (1 - descuento)
            return round(subtotal * (1 + impuesto), 2)
        except ValueError as ve:
            registrar_log(f"Error en cálculo de asesoría {self.codigo}: {ve}", "ERROR")
            raise ServicioError(f"Descuento inválido ({descuento}) al calcular costo de asesoría.") from ve

    def obtener_descripcion(self) -> str:
        return f"Asesoría '{self.area}' ({self.horas} hrs) - Base/h: ${self.costo_base:,.0f}"


class Reserva(EntidadSistema):
    def __init__(self, id_reserva: str, cliente: Cliente, servicio: Servicio):
        if not id_reserva or not id_reserva.strip():
            raise ReservaError("El ID de la reserva no puede estar vacío.")
        if not servicio.disponible:
            raise ReservaError(f"El servicio '{servicio.codigo} - {servicio.nombre}' no está disponible actualmente.")

        self.id_reserva = id_reserva.strip().upper()
        self.cliente = cliente
        self.servicio = servicio
        self.estado = "Pendiente"
        self.costo_total = 0.0

    def procesar_reserva(self, descuento: float = 0.0):
        try:
            if not self.servicio.disponible:
                raise ServicioError(f"El servicio {self.servicio.codigo} ya fue reservado.")
            self.costo_total = self.servicio.calcular_costo(descuento=descuento)
            self.estado = "Confirmada"
            self.servicio.disponible = False  # Bloquea disponibilidad al confirmar
            registrar_log(
                f"Reserva {self.id_reserva} confirmada para {self.cliente.nombre} ({self.servicio.codigo}). Total: ${self.costo_total:,.2f}",
                "ACCION"
            )
        except Exception as e:
            self.estado = "Fallida"
            registrar_log(f"Fallo al procesar reserva {self.id_reserva}: {e}", "ERROR")
            raise ReservaError(f"No se pudo procesar la reserva {self.id_reserva}: {e}") from e

    def cancelar(self):
        if self.estado == "Cancelada":
            raise ReservaError(f"La reserva {self.id_reserva} ya se encuentra cancelada.")
        self.estado = "Cancelada"
        self.servicio.disponible = True  # Libera el servicio nuevamente
        registrar_log(f"Reserva {self.id_reserva} cancelada. Servicio {self.servicio.codigo} liberado.", "AVISO")

    def obtener_info(self) -> str:
        return (
            f"[{self.id_reserva}] Cliente: {self.cliente.nombre} | "
            f"Servicio: {self.servicio.codigo} ({self.servicio.nombre}) | "
            f"Total: ${self.costo_total:,.2f} | Estado: {self.estado}"
        )


# ==========================================
# INTERFAZ GRÁFICA INTERACTIVA (TKINTER)
# ==========================================
class SoftwareFJApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Software FJ - Sistema Integral de Gestión (Fase 4)")
        self.root.geometry("880x660")
        self.root.resizable(False, False)

        self.clientes = []
        self.servicios = []
        self.reservas = []

        self._build_ui()

    def _build_ui(self):
        header = tk.Label(
            self.root,
            text="Software FJ - Gestión Integral de Clientes, Servicios y Reservas",
            font=("Helvetica", 15, "bold"),
            fg="#1E3A8A"
        )
        header.pack(pady=10)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(padx=15, pady=5, fill="both", expand=True)

        # Pestañas
        self.tab_clientes = ttk.Frame(self.notebook)
        self.tab_servicios = ttk.Frame(self.notebook)
        self.tab_reservas = ttk.Frame(self.notebook)
        self.tab_simulacion = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_clientes, text="1. Gestión de Clientes")
        self.notebook.add(self.tab_servicios, text="2. Catálogo de Servicios")
        self.notebook.add(self.tab_reservas, text="3. Gestión de Reservas")
        self.notebook.add(self.tab_simulacion, text="4. Simulación y Logs (10 Pruebas)")

        self._build_tab_clientes()
        self._build_tab_servicios()
        self._build_tab_reservas()
        self._build_tab_simulacion()

    # ---------- PESTAÑA 1: CLIENTES ----------
    def _build_tab_clientes(self):
        form = tk.LabelFrame(self.tab_clientes, text=" Registrar Nuevo Cliente ", font=("Helvetica", 10, "bold"))
        form.pack(padx=15, pady=10, fill="x")

        tk.Label(form, text="Nombre Completo:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.ent_cli_nombre = tk.Entry(form, width=28)
        self.ent_cli_nombre.grid(row=0, column=1, padx=8, pady=6)

        tk.Label(form, text="Cédula:").grid(row=0, column=2, padx=8, pady=6, sticky="e")
        self.ent_cli_cedula = tk.Entry(form, width=22)
        self.ent_cli_cedula.grid(row=0, column=3, padx=8, pady=6)

        tk.Label(form, text="Correo Electrónico:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.ent_cli_correo = tk.Entry(form, width=28)
        self.ent_cli_correo.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(form, text="Teléfono:").grid(row=1, column=2, padx=8, pady=6, sticky="e")
        self.ent_cli_tel = tk.Entry(form, width=22)
        self.ent_cli_tel.grid(row=1, column=3, padx=8, pady=6)

        btn_add_cli = tk.Button(
            form, text="Registrar Cliente", bg="#1E3A8A", fg="white",
            font=("Helvetica", 9, "bold"), command=self.registrar_cliente_ui
        )
        btn_add_cli.grid(row=2, column=0, columnspan=4, pady=10)

        list_frame = tk.LabelFrame(self.tab_clientes, text=" Clientes Registrados ", font=("Helvetica", 10, "bold"))
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.list_clientes = tk.Listbox(list_frame, font=("Consolas", 9))
        self.list_clientes.pack(padx=10, pady=10, fill="both", expand=True)

    def registrar_cliente_ui(self):
        try:
            nombre = self.ent_cli_nombre.get()
            cedula = self.ent_cli_cedula.get()
            correo = self.ent_cli_correo.get()
            tel = self.ent_cli_tel.get()

            if any(c.cedula == cedula.strip() for c in self.clientes):
                raise ClienteError(f"Ya existe un cliente registrado con la cédula {cedula}.")

            nuevo = Cliente(nombre, cedula, correo, tel)
            self.clientes.append(nuevo)
            registrar_log(f"Cliente registrado vía UI: {nuevo.obtener_info()}", "ACCION")
            self._actualizar_vistas()

            self.ent_cli_nombre.delete(0, tk.END)
            self.ent_cli_cedula.delete(0, tk.END)
            self.ent_cli_correo.delete(0, tk.END)
            self.ent_cli_tel.delete(0, tk.END)
            messagebox.showinfo("Éxito", f"Cliente '{nuevo.nombre}' registrado correctamente.")
        except ClienteError as ce:
            registrar_log(f"Validación de cliente fallida en UI: {ce}", "ERROR")
            messagebox.showerror("Error de Validación", str(ce))

    # ---------- PESTAÑA 2: SERVICIOS ----------
    def _build_tab_servicios(self):
        form = tk.LabelFrame(self.tab_servicios, text=" Crear Servicio Especializado ", font=("Helvetica", 10, "bold"))
        form.pack(padx=15, pady=10, fill="x")

        tk.Label(form, text="Tipo de Servicio:").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.cmb_srv_tipo = ttk.Combobox(
            form, state="readonly", width=25,
            values=["Reserva de Sala", "Alquiler de Equipo", "Asesoría Especializada"]
        )
        self.cmb_srv_tipo.current(0)
        self.cmb_srv_tipo.grid(row=0, column=1, padx=8, pady=6)
        self.cmb_srv_tipo.bind("<<ComboboxSelected>>", self._actualizar_labels_servicio)

        tk.Label(form, text="Código (ej. SR-01):").grid(row=0, column=2, padx=8, pady=6, sticky="e")
        self.ent_srv_codigo = tk.Entry(form, width=22)
        self.ent_srv_codigo.grid(row=0, column=3, padx=8, pady=6)

        tk.Label(form, text="Nombre del Servicio:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.ent_srv_nombre = tk.Entry(form, width=28)
        self.ent_srv_nombre.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(form, text="Costo Base ($):").grid(row=1, column=2, padx=8, pady=6, sticky="e")
        self.ent_srv_costo = tk.Entry(form, width=22)
        self.ent_srv_costo.grid(row=1, column=3, padx=8, pady=6)

        self.lbl_extra1 = tk.Label(form, text="Capacidad (personas):")
        self.lbl_extra1.grid(row=2, column=0, padx=8, pady=6, sticky="e")
        self.ent_srv_extra1 = tk.Entry(form, width=28)
        self.ent_srv_extra1.grid(row=2, column=1, padx=8, pady=6)

        self.lbl_extra2 = tk.Label(form, text="Duración (horas):")
        self.lbl_extra2.grid(row=2, column=2, padx=8, pady=6, sticky="e")
        self.ent_srv_extra2 = tk.Entry(form, width=22)
        self.ent_srv_extra2.grid(row=2, column=3, padx=8, pady=6)

        btn_add_srv = tk.Button(
            form, text="Agregar Servicio al Catálogo", bg="#1E3A8A", fg="white",
            font=("Helvetica", 9, "bold"), command=self.crear_servicio_ui
        )
        btn_add_srv.grid(row=3, column=0, columnspan=4, pady=10)

        list_frame = tk.LabelFrame(self.tab_servicios, text=" Portafolio y Disponibilidad ", font=("Helvetica", 10, "bold"))
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.list_servicios = tk.Listbox(list_frame, font=("Consolas", 9))
        self.list_servicios.pack(padx=10, pady=10, fill="both", expand=True)

    def _actualizar_labels_servicio(self, event=None):
        tipo = self.cmb_srv_tipo.get()
        if tipo == "Reserva de Sala":
            self.lbl_extra1.config(text="Capacidad (personas):")
            self.lbl_extra2.config(text="Duración (horas):")
        elif tipo == "Alquiler de Equipo":
            self.lbl_extra1.config(text="Nombre del Equipo:")
            self.lbl_extra2.config(text="Duración (días):")
        else:
            self.lbl_extra1.config(text="Área de Especialidad:")
            self.lbl_extra2.config(text="Duración (horas):")

    def crear_servicio_ui(self):
        try:
            tipo = self.cmb_srv_tipo.get()
            codigo = self.ent_srv_codigo.get().strip().upper()
            nombre = self.ent_srv_nombre.get()
            extra1 = self.ent_srv_extra1.get()

            if any(s.codigo == codigo for s in self.servicios):
                raise ServicioError(f"Ya existe un servicio con el código '{codigo}'.")

            try:
                costo = float(self.ent_srv_costo.get())
                extra2_num = int(self.ent_srv_extra2.get())
            except ValueError as ve:
                raise ServicioError("El costo base y la duración deben ser valores numéricos válidos.") from ve

            if tipo == "Reserva de Sala":
                try:
                    cap = int(extra1)
                except ValueError as ve:
                    raise ServicioError("La capacidad de la sala debe ser un número entero.") from ve
                srv = ReservaSala(codigo, nombre, costo, cap, extra2_num)
            elif tipo == "Alquiler de Equipo":
                srv = AlquilerEquipo(codigo, nombre, costo, extra1, extra2_num)
            else:
                srv = AsesoriaEspecializada(codigo, nombre, costo, extra1, extra2_num)

            self.servicios.append(srv)
            registrar_log(f"Servicio creado vía UI: {srv.obtener_info()}", "ACCION")
            self._actualizar_vistas()

            self.ent_srv_codigo.delete(0, tk.END)
            self.ent_srv_nombre.delete(0, tk.END)
            self.ent_srv_costo.delete(0, tk.END)
            self.ent_srv_extra1.delete(0, tk.END)
            self.ent_srv_extra2.delete(0, tk.END)
            messagebox.showinfo("Éxito", f"Servicio '{srv.nombre}' agregado correctamente.")
        except ServicioError as se:
            registrar_log(f"Error al crear servicio en UI: {se}", "ERROR")
            messagebox.showerror("Error en Servicio", str(se))

    # ---------- PESTAÑA 3: RESERVAS ----------
    def _build_tab_reservas(self):
        form = tk.LabelFrame(self.tab_reservas, text=" Procesar Nueva Reserva ", font=("Helvetica", 10, "bold"))
        form.pack(padx=15, pady=10, fill="x")

        tk.Label(form, text="ID Reserva (ej. RES-01):").grid(row=0, column=0, padx=8, pady=6, sticky="e")
        self.ent_res_id = tk.Entry(form, width=22)
        self.ent_res_id.grid(row=0, column=1, padx=8, pady=6)

        tk.Label(form, text="Descuento (0.0 a 0.5):").grid(row=0, column=2, padx=8, pady=6, sticky="e")
        self.ent_res_desc = tk.Entry(form, width=22)
        self.ent_res_desc.insert(0, "0.0")
        self.ent_res_desc.grid(row=0, column=3, padx=8, pady=6)

        tk.Label(form, text="Seleccionar Cliente:").grid(row=1, column=0, padx=8, pady=6, sticky="e")
        self.cmb_res_cliente = ttk.Combobox(form, state="readonly", width=32)
        self.cmb_res_cliente.grid(row=1, column=1, padx=8, pady=6)

        tk.Label(form, text="Seleccionar Servicio:").grid(row=1, column=2, padx=8, pady=6, sticky="e")
        self.cmb_res_servicio = ttk.Combobox(form, state="readonly", width=32)
        self.cmb_res_servicio.grid(row=1, column=3, padx=8, pady=6)

        btn_frame = tk.Frame(form)
        btn_frame.grid(row=2, column=0, columnspan=4, pady=10)

        tk.Button(
            btn_frame, text="Confirmar Reserva", bg="#10B981", fg="white",
            font=("Helvetica", 9, "bold"), padx=10, command=self.crear_reserva_ui
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, text="Cancelar Reserva Seleccionada", bg="#EF4444", fg="white",
            font=("Helvetica", 9, "bold"), padx=10, command=self.cancelar_reserva_ui
        ).grid(row=0, column=1, padx=10)

        list_frame = tk.LabelFrame(self.tab_reservas, text=" Historial de Reservas ", font=("Helvetica", 10, "bold"))
        list_frame.pack(padx=15, pady=5, fill="both", expand=True)

        self.list_reservas = tk.Listbox(list_frame, font=("Consolas", 9))
        self.list_reservas.pack(padx=10, pady=10, fill="both", expand=True)

    def crear_reserva_ui(self):
        try:
            id_res = self.ent_res_id.get().strip().upper()
            idx_cli = self.cmb_res_cliente.current()
            idx_srv = self.cmb_res_servicio.current()

            if idx_cli < 0 or idx_srv < 0:
                raise ReservaError("Debe seleccionar un cliente y un servicio válidos.")
            if any(r.id_reserva == id_res for r in self.reservas):
                raise ReservaError(f"El ID de reserva '{id_res}' ya existe.")

            try:
                desc = float(self.ent_res_desc.get())
            except ValueError as ve:
                raise ReservaError("El descuento debe ser un número decimal (ej. 0.1 para 10%).") from ve

            cliente = self.clientes[idx_cli]
            servicio = self.servicios[idx_srv]

            reserva = Reserva(id_res, cliente, servicio)
            reserva.procesar_reserva(descuento=desc)
            self.reservas.append(reserva)
            self._actualizar_vistas()

            self.ent_res_id.delete(0, tk.END)
            messagebox.showinfo("Reserva Confirmada", f"Reserva {reserva.id_reserva} confirmada.\nTotal (IVA incluido): ${reserva.costo_total:,.2f}")
        except ReservaError as re:
            # Se registra el error de la interfaz en app_log.txt con tipo ERROR
            registrar_log(f"Error en la interfaz al crear la reserva: {re}", "ERROR")
            messagebox.showerror("Error en Reserva", str(re))

    def cancelar_reserva_ui(self):
        try:
            sel = self.list_reservas.curselection()
            if not sel:
                raise ReservaError("Seleccione una reserva de la lista para cancelar.")
            reserva = self.reservas[sel[0]]
            reserva.cancelar()
            self._actualizar_vistas()
            messagebox.showinfo("Reserva Cancelada", f"La reserva {reserva.id_reserva} fue cancelada y el servicio quedó disponible.")
        except ReservaError as re:
            # Se registra el error de la interfaz en app_log.txt con tipo ERROR
            registrar_log(f"Error en la interfaz al cancelar la reserva: {re}", "ERROR")
            messagebox.showerror("Error al Cancelar", str(re))

    def _actualizar_vistas(self):
        self.list_clientes.delete(0, tk.END)
        for c in self.clientes:
            self.list_clientes.insert(tk.END, c.obtener_info())
        self.cmb_res_cliente["values"] = [f"{c.cedula} - {c.nombre}" for c in self.clientes]

        self.list_servicios.delete(0, tk.END)
        for s in self.servicios:
            self.list_servicios.insert(tk.END, s.obtener_info())
        self.cmb_res_servicio["values"] = [
            f"{s.codigo} - {s.nombre} ({'Disponible' if s.disponible else 'Ocupado'})" for s in self.servicios
        ]

        self.list_reservas.delete(0, tk.END)
        for r in self.reservas:
            self.list_reservas.insert(tk.END, r.obtener_info())

    # ---------- PESTAÑA 4: SIMULACIÓN 10 OPERACIONES ----------
    def _build_tab_simulacion(self):
        log_frame = tk.LabelFrame(self.tab_simulacion, text=" Consola de Simulación y Auditoría (app_log.txt) ", font=("Helvetica", 10, "bold"))
        log_frame.pack(padx=15, pady=10, fill="both", expand=True)

        self.log_text = tk.Text(log_frame, font=("Consolas", 8), height=20, state="disabled", bg="#F8FAFC")
        self.log_text.pack(padx=10, pady=10, fill="both", expand=True)

        btn_frame = tk.Frame(self.tab_simulacion)
        btn_frame.pack(pady=10)

        tk.Button(
            btn_frame, text="Ejecutar Simulación de 10 Operaciones", bg="#10B981", fg="white",
            font=("Helvetica", 10, "bold"), padx=12, pady=6, command=self.ejecutar_simulacion_10_operaciones
        ).grid(row=0, column=0, padx=10)

        tk.Button(
            btn_frame, text="Limpiar Consola", bg="#EF4444", fg="white",
            font=("Helvetica", 10, "bold"), padx=12, pady=6, command=self.limpiar_consola
        ).grid(row=0, column=1, padx=10)

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
        registrar_log("Inicio de simulación automatizada de 10 operaciones.", "SISTEMA")
        operaciones_completadas = 0

        # Op 1: Registro válido de cliente
        try:
            c1 = Cliente("Carlos Pérez", "12345678", "carlos@mail.com", "3001112233")
            if not any(c.cedula == c1.cedula for c in self.clientes):
                self.clientes.append(c1)
            self.log("✅ Op 1 [ÉXITO]: Cliente válido registrado -> " + c1.nombre)
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 1 [FALLÓ]: {e}")

        # Op 2: Registro inválido de cliente (try/except/else/finally)
        try:
            try:
                c_malo = Cliente("Ana Gómez", "abc12345", "correo_invalido", "123")
            except ClienteError as ce:
                self.log(f"⚠️ Op 2 [EXCEPCIÓN CONTROLADA]: Datos de cliente inválidos interceptados -> {ce}")
                raise
            else:
                self.clientes.append(c_malo)
            finally:
                self.log("   -> [Finally Op 2]: Bloque de validación de cliente finalizado.")
        except Exception:
            self.log("✅ Op 2 [ÉXITO EN ROBUSTEZ]: Sistema protegido ante cliente corrupto.")
            operaciones_completadas += 1

        # Op 3: Creación válida de Sala
        try:
            s1 = ReservaSala("SR-SIM1", "Sala Ejecutiva Norte", 50000.0, 10, 3)
            if not any(s.codigo == s1.codigo for s in self.servicios):
                self.servicios.append(s1)
            self.log("✅ Op 3 [ÉXITO]: Servicio de sala creado -> " + s1.obtener_descripcion())
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 3 [FALLÓ]: {e}")

        # Op 4: Creación inválida de Sala (horas negativas)
        try:
            ReservaSala("SR-ERR", "Sala Inválida", 30000.0, 5, -2)
        except ServicioError as se:
            self.log(f"⚠️ Op 4 [EXCEPCIÓN CONTROLADA]: Parámetros negativos rechazados -> {se}")
            self.log("✅ Op 4 [ÉXITO EN ROBUSTEZ]: Creación errónea controlada.")
            operaciones_completadas += 1

        # Op 5: Creación válida de Alquiler de Equipo
        try:
            s2 = AlquilerEquipo("EQ-SIM1", "Kit Audiovisual", 40000.0, "Proyectores 4K", 2)
            if not any(s.codigo == s2.codigo for s in self.servicios):
                self.servicios.append(s2)
            self.log("✅ Op 5 [ÉXITO]: Alquiler de equipo creado -> " + s2.obtener_descripcion())
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 5 [FALLÓ]: {e}")

        # Op 6: Creación válida de Asesoría Especializada
        try:
            s3 = AsesoriaEspecializada("AS-SIM1", "Consultoría TI", 100000.0, "Arquitectura Cloud", 4)
            if not any(s.codigo == s3.codigo for s in self.servicios):
                self.servicios.append(s3)
            self.log("✅ Op 6 [ÉXITO]: Asesoría creada -> " + s3.obtener_descripcion())
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 6 [FALLÓ]: {e}")

        # Op 7: Reserva exitosa (bloquea disponibilidad de SR-SIM1)
        try:
            s_disp = next(s for s in self.servicios if s.codigo == "SR-SIM1")
            s_disp.disponible = True
            res1 = Reserva("RES-SIM1", c1, s_disp)
            res1.procesar_reserva(descuento=0.1)
            self.reservas.append(res1)
            self.log(f"✅ Op 7 [ÉXITO]: Reserva {res1.id_reserva} confirmada. Total: ${res1.costo_total:,.2f}")
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 7 [FALLÓ]: {e}")

        # Op 8: Reserva fallida por descuento fuera de rango (excepción encadenada)
        try:
            s_eq = next(s for s in self.servicios if s.codigo == "EQ-SIM1")
            s_eq.disponible = True
            res_mala = Reserva("RES-SIM2", c1, s_eq)
            res_mala.procesar_reserva(descuento=0.95)
        except ReservaError as re:
            self.log(f"⚠️ Op 8 [EXCEPCIÓN CONTROLADA]: Descuento excesivo capturado -> {re}")
            self.log("✅ Op 8 [ÉXITO EN ROBUSTEZ]: Encadenamiento de excepción verificado.")
            operaciones_completadas += 1

        # Op 9: Cancelación de reserva y liberación de disponibilidad
        try:
            res1.cancelar()
            self.log(f"✅ Op 9 [ÉXITO]: Reserva {res1.id_reserva} cancelada y servicio {res1.servicio.codigo} liberado.")
            operaciones_completadas += 1
        except Exception as e:
            self.log(f"❌ Op 9 [FALLÓ]: {e}")

        # Op 10: Reporte de integridad con try/except/else/finally completo
        try:
            total_cli = len(self.clientes)
            total_srv = len(self.servicios)
            total_res = len(self.reservas)
        except Exception as e:
            self.log(f"❌ Op 10 [FALLÓ]: {e}")
        else:
            self.log(f"✅ Op 10 [ÉXITO]: Integridad verificada -> Clientes: {total_cli} | Servicios: {total_srv} | Reservas: {total_res}.")
            operaciones_completadas += 1
        finally:
            self.log("   -> [Finally Op 10]: Auditoría finalizada sin interrupciones.")

        self._actualizar_vistas()
        self.log(f"\n=== SIMULACIÓN FINALIZADA: {operaciones_completadas}/10 OPERACIONES EXITOSAS Y CONTROLADAS ===")
        registrar_log(f"Simulación finalizada con {operaciones_completadas}/10 operaciones exitosas.", "INFO")
        messagebox.showinfo("Simulación Completa", f"Simulación finalizada: {operaciones_completadas}/10 operaciones exitosas y controladas.")


if __name__ == "__main__":
    registrar_log("Aplicación Software FJ iniciada.", "SISTEMA")
    root = tk.Tk()
    app = SoftwareFJApp(root)
    root.mainloop()
