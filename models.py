from database import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario(db.Model, UserMixin):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    usuario = db.Column(db.String(50), unique=True, nullable=False)
    clave = db.Column(db.String(255), nullable=False)
    rol = db.Column(db.String(50), default="Empleado")
    activo = db.Column(db.Boolean, default=True)

    puede_dashboard = db.Column(db.Boolean, default=True)
    puede_ventas = db.Column(db.Boolean, default=True)
    puede_inventario = db.Column(db.Boolean, default=False)
    puede_caja = db.Column(db.Boolean, default=True)
    puede_fiados = db.Column(db.Boolean, default=False)
    puede_reportes = db.Column(db.Boolean, default=False)
    puede_ganancias = db.Column(db.Boolean, default=False)
    puede_papelera = db.Column(db.Boolean, default=False)
    puede_configuracion = db.Column(db.Boolean, default=False)

    def crear_clave(self, clave):
        self.clave = generate_password_hash(clave)

    def verificar_clave(self, clave):
        return check_password_hash(self.clave, clave)

class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"))
    precio_compra = db.Column(db.Numeric(10, 2), default=0)
    stock = db.Column(db.Integer, default=0)
    stock_minimo = db.Column(db.Integer, default=5)
    activo = db.Column(db.Boolean, default=True)

    categoria = db.relationship("Categoria", backref="productos")


class Presentacion(db.Model):
    __tablename__ = "presentaciones"

    id = db.Column(db.Integer, primary_key=True)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"))
    nombre = db.Column(db.String(50), nullable=False)
    precio = db.Column(db.Numeric(10, 2), nullable=False)

    producto = db.relationship("Producto", backref="presentaciones")


class Venta(db.Model):
    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, server_default=db.func.now())
    total = db.Column(db.Numeric(10, 2), default=0)
    efectivo = db.Column(db.Numeric(10, 2), default=0)
    cambio = db.Column(db.Numeric(10, 2), default=0)


class DetalleVenta(db.Model):
    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer, primary_key=True)
    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"))
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"))
    presentacion_id = db.Column(db.Integer, db.ForeignKey("presentaciones.id"))
    cantidad = db.Column(db.Integer, default=1)
    precio = db.Column(db.Numeric(10, 2), default=0)
    subtotal = db.Column(db.Numeric(10, 2), default=0)

    # Cuentas fiadas de clientes
class Fiado(db.Model):
    __tablename__ = "fiados"

    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(120), nullable=False)
    telefono = db.Column(db.String(30))
    descripcion = db.Column(db.String(255), nullable=False)
    monto_total = db.Column(db.Numeric(10, 2), default=0)
    abono = db.Column(db.Numeric(10, 2), default=0)
    pendiente = db.Column(db.Numeric(10, 2), default=0)
    estado = db.Column(db.String(20), default="Pendiente")
    fecha = db.Column(db.DateTime, server_default=db.func.now())


class Caja(db.Model):
    __tablename__ = "cajas"

    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, server_default=db.func.current_date())
    monto_inicial = db.Column(db.Numeric(10, 2), default=0)
    monto_final = db.Column(db.Numeric(10, 2), default=0)
    total_ventas = db.Column(db.Numeric(10, 2), default=0)
    total_entradas = db.Column(db.Numeric(10, 2), default=0)
    total_salidas = db.Column(db.Numeric(10, 2), default=0)
    estado = db.Column(db.String(20), default="Abierta")


class MovimientoCaja(db.Model):
    __tablename__ = "movimientos_caja"

    id = db.Column(db.Integer, primary_key=True)
    caja_id = db.Column(db.Integer, db.ForeignKey("cajas.id"))
    tipo = db.Column(db.String(20), nullable=False)
    concepto = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.String(200))
    monto = db.Column(db.Numeric(10, 2), default=0)
    fecha = db.Column(db.DateTime, server_default=db.func.now())

    caja = db.relationship("Caja", backref="movimientos")

    

class Cliente(db.Model):
    __tablename__ = "clientes"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, index=True)
    telefono = db.Column(db.String(30))
    direccion = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())


class Proveedor(db.Model):
    __tablename__ = "proveedores"
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, index=True)
    telefono = db.Column(db.String(30))
    correo = db.Column(db.String(120))
    direccion = db.Column(db.String(200))
    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, server_default=db.func.now())


class Compra(db.Model):
    __tablename__ = "compras"
    id = db.Column(db.Integer, primary_key=True)
    proveedor_id = db.Column(db.Integer, db.ForeignKey("proveedores.id"), nullable=True)
    fecha = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    numero_factura = db.Column(db.String(80))
    total = db.Column(db.Numeric(12, 2), default=0, nullable=False)
    observacion = db.Column(db.String(255))
    proveedor = db.relationship("Proveedor", backref="compras")


class DetalleCompra(db.Model):
    __tablename__ = "detalle_compras"
    id = db.Column(db.Integer, primary_key=True)
    compra_id = db.Column(db.Integer, db.ForeignKey("compras.id"), nullable=False)
    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False, default=1)
    costo_unitario = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    subtotal = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    compra = db.relationship("Compra", backref=db.backref("detalles", cascade="all, delete-orphan"))
    producto = db.relationship("Producto", backref="detalles_compra")


class Gasto(db.Model):
    __tablename__ = "gastos"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    categoria = db.Column(db.String(80), nullable=False)
    concepto = db.Column(db.String(150), nullable=False)
    monto = db.Column(db.Numeric(12, 2), nullable=False, default=0)
    metodo_pago = db.Column(db.String(30), default="Efectivo")
    observacion = db.Column(db.String(255))
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    usuario_rel = db.relationship("Usuario", backref="gastos_registrados")


class Auditoria(db.Model):
    __tablename__ = "auditoria"
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, server_default=db.func.now(), index=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    accion = db.Column(db.String(80), nullable=False)
    modulo = db.Column(db.String(80), nullable=False)
    detalle = db.Column(db.String(255))
    usuario_rel = db.relationship("Usuario", backref="auditorias")
