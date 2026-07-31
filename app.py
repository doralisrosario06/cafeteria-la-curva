from flask import (Flask,render_template,redirect,url_for,request,flash,jsonify
)
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from sqlalchemy import func, text
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from functools import wraps
import csv, io, os, sqlite3, tempfile, zipfile
from flask import send_file, abort

from config import Config
from database import db

from models import (
    Usuario,
    Categoria,
    Producto,
    Presentacion,
    Venta,
    DetalleVenta,
    Fiado,
    Caja,
    MovimientoCaja,
    Cliente, Proveedor, Compra, DetalleCompra, Gasto, Auditoria
)


app = Flask(__name__)
app.config.from_object(Config)

# Hace que las conexiones viejas se comprueben antes de reutilizarlas y
# evita que PostgreSQL deje la aplicación esperando indefinidamente.
engine_options = dict(app.config.get("SQLALCHEMY_ENGINE_OPTIONS") or {})
engine_options.setdefault("pool_pre_ping", True)
if str(app.config.get("SQLALCHEMY_DATABASE_URI", "")).startswith("postgres"):
    connect_args = dict(engine_options.get("connect_args") or {})
    connect_args.setdefault("connect_timeout", 5)
    engine_options.setdefault("pool_recycle", 300)
    engine_options["connect_args"] = connect_args
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = engine_options

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"


@login_manager.user_loader
def cargar_usuario(user_id):
    try:
        return db.session.get(Usuario, int(user_id))
    except (TypeError, ValueError):
        return None


def crear_admin():
    admin = Usuario.query.filter_by(usuario="admin").first()

    if not admin:
        admin = Usuario(nombre="Administrador", usuario="admin", rol="Administrador")
        admin.crear_clave(os.getenv("ADMIN_PASSWORD", "1234"))
        db.session.add(admin)

    # El administrador siempre debe ver y utilizar todos los módulos.
    admin.rol = "Administrador"
    admin.activo = True
    for campo in (
        "puede_dashboard", "puede_ventas", "puede_inventario",
        "puede_caja", "puede_fiados", "puede_reportes",
        "puede_ganancias", "puede_papelera", "puede_configuracion"
    ):
        setattr(admin, campo, True)
    db.session.commit()


def crear_categorias():
    categorias = [
        "Café",
        "Jugos",
        "Batidas",
        "Sandwiches",
        "Desayunos",
        "Postres",
        "Bebidas"
    ]

    for nombre in categorias:
        existe = Categoria.query.filter_by(nombre=nombre).first()

        if not existe:
            db.session.add(Categoria(nombre=nombre))

    db.session.commit()


def permiso_requerido(campo):
    def decorador(funcion):
        @wraps(funcion)
        @login_required
        def envuelta(*args, **kwargs):
            if current_user.rol == "Administrador" or getattr(current_user, campo, False):
                return funcion(*args, **kwargs)
            flash("No tienes permiso para entrar a este módulo.", "danger")
            return redirect(url_for("dashboard"))
        return envuelta
    return decorador


def dinero(valor, defecto="0"):
    try:
        numero = Decimal(str(valor if valor not in (None, "") else defecto))
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError("Monto no válido")
    return numero.quantize(Decimal("0.01"))


def registrar_auditoria(accion, modulo, detalle=""):
    try:
        db.session.add(Auditoria(
            usuario_id=current_user.id if current_user.is_authenticated else None,
            accion=accion,
            modulo=modulo,
            detalle=str(detalle)[:255]
        ))
    except Exception:
        pass


@app.route("/", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))

    if request.method == "POST":
        usuario = request.form.get("usuario")
        clave = request.form.get("clave")

        user = Usuario.query.filter_by(usuario=usuario, activo=True).first()

        if user and user.verificar_clave(clave):
            login_user(user)
            return redirect(url_for("dashboard"))

        flash("Usuario o contraseña incorrectos")

    return render_template("login.html")


@app.route("/dashboard")
@login_required
def dashboard():
    hoy = date.today()

    ventas_hoy = db.session.query(
        func.coalesce(func.sum(Venta.total), 0)
    ).filter(func.date(Venta.fecha) == hoy).scalar()

    total_productos = Producto.query.filter_by(activo=True).count()

    fiados_pendientes = db.session.query(
        func.coalesce(func.sum(Fiado.pendiente), 0)
    ).filter_by(estado="Pendiente").scalar()

    caja_abierta = Caja.query.filter_by(fecha=hoy, estado="Abierta").first()

    ultimas_ventas = Venta.query.order_by(Venta.id.desc()).limit(5).all()

    return render_template(
        "dashboard.html",
        ventas_hoy=float(ventas_hoy),
        total_productos=total_productos,
        fiados_pendientes=float(fiados_pendientes),
        caja_abierta=caja_abierta,
        ultimas_ventas=ultimas_ventas
    )


@app.route("/ventas")
@login_required
def ventas():
    categorias = Categoria.query.all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre.asc()).all()

    return render_template(
        "ventas.html",
        categorias=categorias,
        productos=productos
    )

@app.route("/ventas/finalizar", methods=["POST"])
@login_required
def finalizar_venta():
    datos = request.get_json(silent=True) or {}

    carrito = datos.get("carrito", [])
    tipo_pago = str(
        datos.get("tipo_pago", "Efectivo")
    ).strip()

    if not carrito:
        return jsonify({
            "ok": False,
            "mensaje": "No hay productos en el carrito."
        }), 400

    if tipo_pago not in ["Efectivo", "Fiado"]:
        return jsonify({
            "ok": False,
            "mensaje": "La forma de pago no es válida."
        }), 400

    productos_procesados = []
    total = 0.0

    # Verifica todo antes de modificar la base de datos
    for item in carrito:
        try:
            producto_id = int(item.get("producto_id"))
            presentacion_id = int(
                item.get("presentacion_id")
            )
            cantidad = int(item.get("cantidad", 0))
        except (TypeError, ValueError):
            return jsonify({
                "ok": False,
                "mensaje": "Los datos de un producto no son válidos."
            }), 400

        producto = db.session.get(
            Producto,
            producto_id
        )

        presentacion = db.session.get(
            Presentacion,
            presentacion_id
        )

        if not producto or not producto.activo:
            return jsonify({
                "ok": False,
                "mensaje": (
                    "Uno de los productos ya no está disponible."
                )
            }), 400

        if not presentacion:
            return jsonify({
                "ok": False,
                "mensaje": (
                    f"La presentación de {producto.nombre} "
                    "no existe."
                )
            }), 400

        if presentacion.producto_id != producto.id:
            return jsonify({
                "ok": False,
                "mensaje": (
                    "La presentación seleccionada "
                    "no pertenece al producto."
                )
            }), 400

        if cantidad <= 0:
            return jsonify({
                "ok": False,
                "mensaje": "La cantidad debe ser mayor que cero."
            }), 400

        if producto.stock < cantidad:
            return jsonify({
                "ok": False,
                "mensaje": (
                    f"Stock insuficiente para "
                    f"{producto.nombre}. "
                    f"Disponibles: {producto.stock}."
                )
            }), 400

        precio = float(presentacion.precio or 0)
        subtotal = precio * cantidad

        total += subtotal

        productos_procesados.append({
            "producto": producto,
            "presentacion": presentacion,
            "cantidad": cantidad,
            "precio": precio,
            "subtotal": subtotal
        })

    efectivo = 0.0
    cambio = 0.0
    abono_inicial = 0.0
    nombre_cliente = ""
    telefono = ""

    if tipo_pago == "Efectivo":
        try:
            efectivo = float(
                datos.get("efectivo") or 0
            )
        except (TypeError, ValueError):
            return jsonify({
                "ok": False,
                "mensaje": "El efectivo recibido no es válido."
            }), 400

        if efectivo < total:
            return jsonify({
                "ok": False,
                "mensaje": "El efectivo recibido no alcanza."
            }), 400

        cambio = efectivo - total

    else:
        nombre_cliente = str(
            datos.get("nombre_cliente") or ""
        ).strip()

        telefono = str(
            datos.get("telefono") or ""
        ).strip()

        try:
            abono_inicial = float(
                datos.get("abono_inicial") or 0
            )
        except (TypeError, ValueError):
            return jsonify({
                "ok": False,
                "mensaje": "El abono inicial no es válido."
            }), 400

        if not nombre_cliente:
            return jsonify({
                "ok": False,
                "mensaje": (
                    "Debes escribir el nombre del cliente."
                )
            }), 400

        if abono_inicial < 0:
            return jsonify({
                "ok": False,
                "mensaje": (
                    "El abono inicial no puede ser negativo."
                )
            }), 400

        if abono_inicial > total:
            return jsonify({
                "ok": False,
                "mensaje": (
                    "El abono no puede superar "
                    "el total de la venta."
                )
            }), 400

        # En un fiado solo se recibe el abono
        efectivo = abono_inicial
        cambio = 0.0

    try:
        # Guarda la cabecera de la venta
        venta = Venta(
            total=total,
            efectivo=efectivo,
            cambio=cambio
        )

        db.session.add(venta)
        db.session.flush()

        descripcion_productos = []

        # Guarda los detalles y descuenta inventario
        for item in productos_procesados:
            producto = item["producto"]
            presentacion = item["presentacion"]

            producto.stock -= item["cantidad"]

            detalle = DetalleVenta(
                venta_id=venta.id,
                producto_id=producto.id,
                presentacion_id=presentacion.id,
                cantidad=item["cantidad"],
                precio=item["precio"],
                subtotal=item["subtotal"]
            )

            db.session.add(detalle)

            descripcion_productos.append(
                f'{item["cantidad"]} x '
                f'{producto.nombre} '
                f'({presentacion.nombre})'
            )

        fiado_id = None
        pendiente = 0.0

        # Crea automáticamente la cuenta fiada
        if tipo_pago == "Fiado":
            pendiente = total - abono_inicial

            fiado = Fiado(
                nombre_cliente=nombre_cliente,
                telefono=telefono,
                descripcion=", ".join(
                    descripcion_productos
                ),
                monto_total=total,
                abono=abono_inicial,
                pendiente=pendiente,
                estado=(
                    "Pagado"
                    if pendiente <= 0
                    else "Pendiente"
                )
            )

            db.session.add(fiado)
            db.session.flush()

            fiado_id = fiado.id

        db.session.commit()

        return jsonify({
            "ok": True,
            "mensaje": (
                "Venta fiada registrada correctamente."
                if tipo_pago == "Fiado"
                else "Venta realizada correctamente."
            ),
            "venta_id": venta.id,
            "fiado_id": fiado_id,
            "tipo_pago": tipo_pago,
            "total": round(total, 2),
            "efectivo": round(efectivo, 2),
            "abono": round(abono_inicial, 2),
            "pendiente": round(pendiente, 2),
            "cambio": round(cambio, 2)
        })

    except Exception as error:
        db.session.rollback()

        print(
            "Error al finalizar la venta:",
            error
        )

        return jsonify({
            "ok": False,
            "mensaje": (
                "Ocurrió un error al guardar la venta."
            )
        }), 500

@app.route("/inventario", methods=["GET", "POST"])
@login_required
def inventario():
    if request.method == "POST":
        producto = Producto(
            nombre=request.form.get("nombre"),
            categoria_id=request.form.get("categoria_id"),
            precio_compra=request.form.get("precio_compra"),
            stock=request.form.get("stock"),
            stock_minimo=request.form.get("stock_minimo")
        )

        db.session.add(producto)
        db.session.commit()

        tipo_precio = request.form.get("tipo_precio")

        if tipo_precio == "Precio único":
            db.session.add(Presentacion(
                producto_id=producto.id,
                nombre="Único",
                precio=request.form.get("precio_unico")
            ))
        else:
            db.session.add(Presentacion(
                producto_id=producto.id,
                nombre="Pequeño",
                precio=request.form.get("precio_pequeno")
            ))

            db.session.add(Presentacion(
                producto_id=producto.id,
                nombre="Grande",
                precio=request.form.get("precio_grande")
            ))

        db.session.commit()

        flash("Producto guardado correctamente")
        return redirect(url_for("inventario"))

    categorias = Categoria.query.all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.id.desc()).all()

    return render_template(
        "inventario.html",
        categorias=categorias,
        productos=productos
    )


@app.route("/inventario/editar/<int:id>", methods=["GET", "POST"])
@login_required
def editar_producto(id):
    producto = Producto.query.get_or_404(id)
    categorias = Categoria.query.all()

    if request.method == "POST":
        producto.nombre = request.form.get("nombre")
        producto.categoria_id = request.form.get("categoria_id")
        producto.precio_compra = request.form.get("precio_compra")
        producto.stock = request.form.get("stock")
        producto.stock_minimo = request.form.get("stock_minimo")

        presentaciones = producto.presentaciones

        if len(presentaciones) == 1:
            precio_unico = request.form.get("precio_unico")

            if precio_unico:
                presentaciones[0].precio = precio_unico

        elif len(presentaciones) >= 2:
            precio_pequeno = request.form.get("precio_pequeno")
            precio_grande = request.form.get("precio_grande")

            if precio_pequeno:
                presentaciones[0].precio = precio_pequeno

            if precio_grande:
                presentaciones[1].precio = precio_grande

        db.session.commit()

        flash("Producto actualizado correctamente")
        return redirect(url_for("inventario"))

    return render_template(
        "editar_producto.html",
        producto=producto,
        categorias=categorias
    )


@app.route("/inventario/eliminar/<int:id>", methods=["POST"])
@login_required
def eliminar_producto(id):
    producto = Producto.query.get_or_404(id)
    producto.activo = False

    db.session.commit()

    flash("Producto enviado a papelera")
    return redirect(url_for("inventario"))


@app.route("/fiados", methods=["GET", "POST"])
@login_required
def fiados():
    if request.method == "POST":
        nombre_cliente = request.form.get("nombre_cliente")
        telefono = request.form.get("telefono")
        descripcion = request.form.get("descripcion")
        monto_total = float(request.form.get("monto_total"))
        abono = float(request.form.get("abono") or 0)

        pendiente = monto_total - abono
        estado = "Pagado" if pendiente <= 0 else "Pendiente"

        fiado = Fiado(
            nombre_cliente=nombre_cliente,
            telefono=telefono,
            descripcion=descripcion,
            monto_total=monto_total,
            abono=abono,
            pendiente=pendiente,
            estado=estado
        )

        db.session.add(fiado)
        db.session.commit()

        flash("Fiado registrado correctamente")
        return redirect(url_for("fiados"))

    buscar = request.args.get("buscar", "")

    consulta = Fiado.query

    if buscar:
        consulta = consulta.filter(Fiado.nombre_cliente.ilike(f"%{buscar}%"))

    pendientes = consulta.filter_by(estado="Pendiente").order_by(Fiado.id.desc()).all()
    pagados = consulta.filter_by(estado="Pagado").order_by(Fiado.id.desc()).all()

    return render_template(
        "fiados.html",
        pendientes=pendientes,
        pagados=pagados,
        buscar=buscar
    )


@app.route("/fiados/pagar/<int:id>", methods=["POST"])
@login_required
def pagar_fiado(id):
    fiado = Fiado.query.get_or_404(id)

    monto_abono = float(request.form.get("abono_extra") or 0)

    fiado.abono = float(fiado.abono) + monto_abono
    fiado.pendiente = float(fiado.monto_total) - float(fiado.abono)

    if fiado.pendiente <= 0:
        fiado.pendiente = 0
        fiado.estado = "Pagado"
    else:
        fiado.estado = "Pendiente"

    db.session.commit()

    flash("Abono registrado correctamente")
    return redirect(url_for("fiados"))


@app.route("/caja", methods=["GET", "POST"])
@login_required
def caja():
    hoy = date.today()

    caja_abierta = Caja.query.filter_by(fecha=hoy, estado="Abierta").first()

    ventas_dia = db.session.query(
        func.coalesce(func.sum(Venta.total), 0)
    ).filter(func.date(Venta.fecha) == hoy).scalar()

    if request.method == "POST":
        accion = request.form.get("accion")

        if accion == "abrir":
            monto_inicial = float(request.form.get("monto_inicial") or 0)

            if caja_abierta:
                flash("Ya existe una caja abierta para hoy")
                return redirect(url_for("caja"))

            nueva_caja = Caja(
                fecha=hoy,
                monto_inicial=monto_inicial,
                estado="Abierta"
            )

            db.session.add(nueva_caja)
            db.session.commit()

            movimiento = MovimientoCaja(
                caja_id=nueva_caja.id,
                tipo="Entrada",
                concepto="Apertura",
                descripcion="Monto inicial del día",
                monto=monto_inicial
            )

            db.session.add(movimiento)
            db.session.commit()

            flash("Caja abierta correctamente")
            return redirect(url_for("caja"))

        if accion == "movimiento":
            if not caja_abierta:
                flash("Primero debes abrir la caja")
                return redirect(url_for("caja"))

            tipo = request.form.get("tipo")
            concepto = request.form.get("concepto")
            descripcion = request.form.get("descripcion")
            monto = float(request.form.get("monto") or 0)

            movimiento = MovimientoCaja(
                caja_id=caja_abierta.id,
                tipo=tipo,
                concepto=concepto,
                descripcion=descripcion,
                monto=monto
            )

            if tipo == "Entrada":
                caja_abierta.total_entradas = float(caja_abierta.total_entradas) + monto
            else:
                caja_abierta.total_salidas = float(caja_abierta.total_salidas) + monto

            db.session.add(movimiento)
            db.session.commit()

            flash("Movimiento registrado correctamente")
            return redirect(url_for("caja"))

        if accion == "cerrar":
            if not caja_abierta:
                flash("No hay caja abierta")
                return redirect(url_for("caja"))

            monto_final = float(request.form.get("monto_final") or 0)

            caja_abierta.total_ventas = ventas_dia
            caja_abierta.monto_final = monto_final
            caja_abierta.estado = "Cerrada"

            db.session.commit()

            flash("Caja cerrada correctamente")
            return redirect(url_for("caja"))

    movimientos = []

    if caja_abierta:
        movimientos = MovimientoCaja.query.filter_by(
            caja_id=caja_abierta.id
        ).order_by(MovimientoCaja.id.desc()).all()

    total_entradas = float(caja_abierta.total_entradas) if caja_abierta else 0
    total_salidas = float(caja_abierta.total_salidas) if caja_abierta else 0
    monto_inicial = float(caja_abierta.monto_inicial) if caja_abierta else 0

    caja_actual = monto_inicial + float(ventas_dia) + total_entradas - total_salidas

    return render_template(
        "caja.html",
        caja_abierta=caja_abierta,
        ventas_dia=float(ventas_dia),
        movimientos=movimientos,
        caja_actual=caja_actual,
        total_salidas=total_salidas
    )


@app.route("/reportes/caja")
@login_required
def reporte_caja():
    fecha_texto = request.args.get("fecha")

    if fecha_texto:
        fecha_busqueda = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    else:
        fecha_busqueda = date.today()

    cajas = Caja.query.filter_by(fecha=fecha_busqueda).order_by(Caja.id.desc()).all()

    ventas_dia = db.session.query(
        func.coalesce(func.sum(Venta.total), 0)
    ).filter(func.date(Venta.fecha) == fecha_busqueda).scalar()

    movimientos = []

    if cajas:
        ids_cajas = [caja.id for caja in cajas]

        movimientos = MovimientoCaja.query.filter(
            MovimientoCaja.caja_id.in_(ids_cajas)
        ).order_by(MovimientoCaja.id.desc()).all()

    monto_inicial = sum(float(caja.monto_inicial) for caja in cajas)
    total_entradas = sum(float(caja.total_entradas) for caja in cajas)
    total_salidas = sum(float(caja.total_salidas) for caja in cajas)
    monto_final = sum(
        float(caja.monto_final)
        for caja in cajas
        if caja.estado == "Cerrada"
    )

    total_esperado = monto_inicial + float(ventas_dia) + total_entradas - total_salidas
    diferencia = monto_final - total_esperado if monto_final > 0 else 0

    return render_template(
        "reporte_caja.html",
        fecha_busqueda=fecha_busqueda,
        cajas=cajas,
        movimientos=movimientos,
        ventas_dia=float(ventas_dia),
        monto_inicial=monto_inicial,
        total_entradas=total_entradas,
        total_salidas=total_salidas,
        monto_final=monto_final,
        total_esperado=total_esperado,
        diferencia=diferencia
    )


@app.route("/reportes")
@login_required
def reportes():
    fecha_texto = request.args.get("fecha")

    if fecha_texto:
        fecha_busqueda = datetime.strptime(fecha_texto, "%Y-%m-%d").date()
    else:
        fecha_busqueda = date.today()

    ventas = Venta.query.filter(
        func.date(Venta.fecha) == fecha_busqueda
    ).order_by(Venta.id.desc()).all()

    facturas = []
    total_vendido = 0
    total_productos = 0

    for venta in ventas:
        detalles = db.session.query(
            DetalleVenta,
            Producto,
            Presentacion
        ).join(
            Producto,
            DetalleVenta.producto_id == Producto.id
        ).join(
            Presentacion,
            DetalleVenta.presentacion_id == Presentacion.id
        ).filter(
            DetalleVenta.venta_id == venta.id
        ).all()

        lista_detalles = []

        for detalle, producto, presentacion in detalles:
            lista_detalles.append({
                "producto": producto.nombre,
                "presentacion": presentacion.nombre,
                "cantidad": detalle.cantidad,
                "precio": detalle.precio,
                "subtotal": detalle.subtotal
            })

            total_productos += int(detalle.cantidad)

        total_vendido += float(venta.total)

        facturas.append({
            "venta": venta,
            "detalles": lista_detalles
        })

    return render_template(
        "reportes.html",
        fecha_busqueda=fecha_busqueda,
        facturas=facturas,
        total_vendido=total_vendido,
        total_facturas=len(ventas),
        total_productos=total_productos
    )


@app.route("/ganancias")
@login_required
def ganancias():
    ingresos = db.session.query(
        func.coalesce(func.sum(Venta.total), 0)
    ).scalar()

    costos = db.session.query(
        func.coalesce(func.sum(DetalleVenta.cantidad * Producto.precio_compra), 0)
    ).join(
        Producto,
        DetalleVenta.producto_id == Producto.id
    ).scalar()

    fiados_pendientes = db.session.query(
        func.coalesce(func.sum(Fiado.pendiente), 0)
    ).filter_by(estado="Pendiente").scalar()

    fiados_pagados = db.session.query(
        func.coalesce(func.sum(Fiado.monto_total), 0)
    ).filter_by(estado="Pagado").scalar()

    gastos_total = db.session.query(func.coalesce(func.sum(Gasto.monto), 0)).scalar()
    ganancia_neta = float(ingresos) - float(costos) - float(gastos_total)
    reserva = max(ganancia_neta, 0) * 0.20
    reinversion = ganancia_neta * 0.30
    disponible = ganancia_neta - reserva - reinversion

    historial = db.session.query(
        func.date(Venta.fecha).label("fecha"),
        func.coalesce(func.sum(Venta.total), 0).label("ingresos")
    ).group_by(
        func.date(Venta.fecha)
    ).order_by(
        func.date(Venta.fecha).desc()
    ).all()

    return render_template(
        "ganancias.html",
        ingresos=float(ingresos),
        costos=float(costos),
        gastos_total=float(gastos_total),
        ganancia_neta=ganancia_neta,
        reserva=reserva,
        reinversion=reinversion,
        disponible=disponible,
        fiados_pendientes=float(fiados_pendientes),
        fiados_pagados=float(fiados_pagados),
        historial=historial
    )

@app.route("/papelera")
@login_required
def papelera():
    productos_eliminados = Producto.query.filter_by(activo=False).order_by(Producto.id.desc()).all()

    return render_template(
        "papelera.html",
        productos_eliminados=productos_eliminados
    )


@app.route("/papelera/restaurar-producto/<int:id>", methods=["POST"])
@login_required
def restaurar_producto(id):
    producto = Producto.query.get_or_404(id)
    producto.activo = True

    db.session.commit()

    flash("Producto restaurado correctamente")
    return redirect(url_for("papelera"))
@app.route("/configuracion", methods=["GET", "POST"])
@login_required
def configuracion():
    if request.method == "POST":
        accion = request.form.get("accion", "crear_usuario")

        if accion in {"cambiar_estado", "eliminar_usuario"}:
            try:
                usuario_id = int(request.form.get("usuario_id", 0))
            except (TypeError, ValueError):
                flash("El usuario indicado no es válido", "danger")
                return redirect(url_for("configuracion"))

            usuario_obj = db.session.get(Usuario, usuario_id)
            if not usuario_obj:
                flash("El usuario no existe", "danger")
                return redirect(url_for("configuracion"))

            if usuario_obj.id == current_user.id:
                flash("No puedes desactivar ni eliminar tu propia cuenta", "warning")
                return redirect(url_for("configuracion"))

            if accion == "cambiar_estado":
                usuario_obj.activo = not usuario_obj.activo
                db.session.commit()
                flash("Estado del usuario actualizado correctamente", "success")
            else:
                db.session.delete(usuario_obj)
                db.session.commit()
                flash("Usuario eliminado correctamente", "success")

            return redirect(url_for("configuracion"))

        nombre = (request.form.get("nombre") or "").strip()
        usuario = (request.form.get("usuario") or "").strip()
        clave = request.form.get("clave") or ""
        rol = (request.form.get("rol") or "Empleado").strip()

        if not nombre or not usuario or not clave:
            flash("Completa nombre, usuario y contraseña", "danger")
            return redirect(url_for("configuracion"))

        existe = Usuario.query.filter_by(usuario=usuario).first()

        if existe:
            flash("Ese usuario ya existe")
            return redirect(url_for("configuracion"))

        nuevo_usuario = Usuario(
            nombre=nombre,
            usuario=usuario,
            rol=rol,
            activo=True,
            puede_dashboard=True,
            puede_ventas=True if request.form.get("puede_ventas") else False,
            puede_inventario=True if request.form.get("puede_inventario") else False,
            puede_caja=True if request.form.get("puede_caja") else False,
            puede_fiados=True if request.form.get("puede_fiados") else False,
            puede_reportes=True if request.form.get("puede_reportes") else False,
            puede_ganancias=True if request.form.get("puede_ganancias") else False,
            puede_papelera=True if request.form.get("puede_papelera") else False,
            puede_configuracion=True if request.form.get("puede_configuracion") else False
        )

        if rol == "Administrador":
            nuevo_usuario.puede_dashboard = True
            nuevo_usuario.puede_ventas = True
            nuevo_usuario.puede_inventario = True
            nuevo_usuario.puede_caja = True
            nuevo_usuario.puede_fiados = True
            nuevo_usuario.puede_reportes = True
            nuevo_usuario.puede_ganancias = True
            nuevo_usuario.puede_papelera = True
            nuevo_usuario.puede_configuracion = True

        nuevo_usuario.crear_clave(clave)

        db.session.add(nuevo_usuario)
        db.session.commit()

        flash("Usuario agregado correctamente")
        return redirect(url_for("configuracion"))

    usuarios = Usuario.query.order_by(Usuario.id.desc()).all()

    return render_template("configuracion.html", usuarios=usuarios)


@app.route("/clientes", methods=["GET", "POST"])
@permiso_requerido("puede_fiados")
def clientes():
    if request.method == "POST":
        nombre=(request.form.get("nombre") or "").strip()
        if not nombre:
            flash("Escribe el nombre del cliente.", "danger")
        else:
            db.session.add(Cliente(nombre=nombre, telefono=(request.form.get("telefono") or "").strip(), direccion=(request.form.get("direccion") or "").strip()))
            registrar_auditoria("Crear", "Clientes", nombre)
            db.session.commit(); flash("Cliente guardado.", "success")
        return redirect(url_for("clientes"))
    buscar=(request.args.get("buscar") or "").strip()
    q=Cliente.query.filter_by(activo=True)
    if buscar: q=q.filter(Cliente.nombre.ilike(f"%{buscar}%"))
    return render_template("clientes.html", clientes=q.order_by(Cliente.nombre).all(), buscar=buscar)


@app.route("/clientes/<int:id>/eliminar", methods=["POST"])
@permiso_requerido("puede_fiados")
def eliminar_cliente(id):
    obj=Cliente.query.get_or_404(id); obj.activo=False
    registrar_auditoria("Desactivar", "Clientes", obj.nombre); db.session.commit()
    flash("Cliente enviado a inactivos.", "success"); return redirect(url_for("clientes"))


@app.route("/proveedores", methods=["GET", "POST"])
@permiso_requerido("puede_inventario")
def proveedores():
    if request.method == "POST":
        nombre=(request.form.get("nombre") or "").strip()
        if not nombre: flash("Escribe el nombre del proveedor.", "danger")
        else:
            db.session.add(Proveedor(nombre=nombre, telefono=(request.form.get("telefono") or "").strip(), correo=(request.form.get("correo") or "").strip(), direccion=(request.form.get("direccion") or "").strip()))
            registrar_auditoria("Crear", "Proveedores", nombre); db.session.commit(); flash("Proveedor guardado.", "success")
        return redirect(url_for("proveedores"))
    return render_template("proveedores.html", proveedores=Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all())


@app.route("/compras", methods=["GET", "POST"])
@permiso_requerido("puede_inventario")
def compras():
    if request.method == "POST":
        try:
            producto=Producto.query.get_or_404(int(request.form.get("producto_id")))
            cantidad=int(request.form.get("cantidad") or 0); costo=dinero(request.form.get("costo_unitario"))
            if cantidad <= 0 or costo < 0: raise ValueError
            proveedor_id=request.form.get("proveedor_id") or None
            compra=Compra(proveedor_id=proveedor_id, numero_factura=(request.form.get("numero_factura") or "").strip(), total=costo*cantidad, observacion=(request.form.get("observacion") or "").strip())
            db.session.add(compra); db.session.flush()
            db.session.add(DetalleCompra(compra_id=compra.id, producto_id=producto.id, cantidad=cantidad, costo_unitario=costo, subtotal=costo*cantidad))
            producto.stock=int(producto.stock or 0)+cantidad; producto.precio_compra=costo
            registrar_auditoria("Registrar", "Compras", f"{cantidad} x {producto.nombre}")
            db.session.commit(); flash("Compra registrada y existencia actualizada.", "success")
        except Exception:
            db.session.rollback(); flash("Revisa el producto, cantidad y costo.", "danger")
        return redirect(url_for("compras"))
    return render_template("compras.html", compras=Compra.query.order_by(Compra.id.desc()).limit(100).all(), productos=Producto.query.filter_by(activo=True).order_by(Producto.nombre).all(), proveedores=Proveedor.query.filter_by(activo=True).order_by(Proveedor.nombre).all())


@app.route("/gastos", methods=["GET", "POST"])
@permiso_requerido("puede_ganancias")
def gastos():
    if request.method == "POST":
        try:
            monto=dinero(request.form.get("monto")); concepto=(request.form.get("concepto") or "").strip(); categoria=(request.form.get("categoria") or "Otros").strip()
            if monto <= 0 or not concepto: raise ValueError
            gasto=Gasto(categoria=categoria, concepto=concepto, monto=monto, metodo_pago=(request.form.get("metodo_pago") or "Efectivo"), observacion=(request.form.get("observacion") or "").strip(), usuario_id=current_user.id)
            db.session.add(gasto)
            caja_abierta=Caja.query.filter_by(fecha=date.today(), estado="Abierta").first()
            if caja_abierta and gasto.metodo_pago == "Efectivo":
                db.session.add(MovimientoCaja(caja_id=caja_abierta.id, tipo="Salida", concepto="Gasto", descripcion=concepto, monto=monto)); caja_abierta.total_salidas=Decimal(str(caja_abierta.total_salidas or 0))+monto
            registrar_auditoria("Registrar", "Gastos", f"{concepto}: {monto}"); db.session.commit(); flash("Gasto registrado.", "success")
        except Exception:
            db.session.rollback(); flash("Completa correctamente el concepto y el monto.", "danger")
        return redirect(url_for("gastos"))
    return render_template("gastos.html", gastos=Gasto.query.order_by(Gasto.id.desc()).limit(200).all())


@app.route("/auditoria")
@permiso_requerido("puede_configuracion")
def auditoria():
    return render_template("auditoria.html", registros=Auditoria.query.order_by(Auditoria.id.desc()).limit(300).all())


@app.route("/respaldo")
@permiso_requerido("puede_configuracion")
def respaldo():
    uri=app.config["SQLALCHEMY_DATABASE_URI"]
    if not uri.startswith("sqlite:///"):
        flash("En PostgreSQL usa las copias automáticas del proveedor de nube.", "info")
        return redirect(url_for("configuracion"))
    db.session.commit(); ruta=uri.replace("sqlite:///", "", 1)
    memoria=io.BytesIO()
    with zipfile.ZipFile(memoria, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(ruta, arcname=f"cafeteria_respaldo_{datetime.now():%Y%m%d_%H%M%S}.db")
    memoria.seek(0)
    registrar_auditoria("Descargar", "Respaldos", "Copia SQLite"); db.session.commit()
    return send_file(memoria, as_attachment=True, download_name=f"respaldo_cafeteria_{datetime.now():%Y%m%d_%H%M%S}.zip", mimetype="application/zip")


@app.route("/manifest.webmanifest")
def manifest():
    return app.send_static_file("manifest.webmanifest")


@app.route("/service-worker.js")
def service_worker():
    respuesta=app.send_static_file("service-worker.js")
    respuesta.headers["Service-Worker-Allowed"]="/"
    respuesta.headers["Cache-Control"]="no-cache"
    return respuesta


@app.route("/salud")
def salud():
    try:
        db.session.execute(text("SELECT 1"))
        return jsonify(ok=True, app="Cafetería La Curva", database="connected")
    except Exception:
        db.session.rollback()
        return jsonify(ok=False, app="Cafetería La Curva", database="disconnected"), 503


@app.after_request
def encabezados_seguridad(response):
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "SAMEORIGIN")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    response.headers.setdefault("Permissions-Policy", "camera=(), microphone=(), geolocation=()")
    if request.is_secure:
        response.headers.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    return response


@app.errorhandler(404)
def pagina_no_encontrada(error):
    if request.path.startswith("/api/"):
        return jsonify(ok=False, mensaje="Recurso no encontrado"), 404
    flash("La página solicitada no existe.", "warning")
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))


@app.errorhandler(500)
def error_interno(error):
    db.session.rollback()
    if request.path.startswith("/api/"):
        return jsonify(ok=False, mensaje="Ocurrió un error interno"), 500
    flash("Ocurrió un error interno. Intenta nuevamente.", "danger")
    return redirect(url_for("dashboard" if current_user.is_authenticated else "login"))

@app.route("/salir")
@login_required
def salir():
    logout_user()
    return redirect(url_for("login"))


def inicializar_base_datos():
    """Comprueba la conexión y prepara las tablas iniciales del sistema."""
    print("Comprobando conexión con la base de datos...", flush=True)

    try:
        # Fuerza una conexión real para mostrar rápido cualquier problema.
        db.session.execute(text("SELECT 1"))

        print("Conexión con la base de datos correcta.", flush=True)
        print("Verificando tablas y datos iniciales...", flush=True)

        db.create_all()
        crear_admin()
        crear_categorias()

        print("Base de datos preparada correctamente.", flush=True)

    except OperationalError as error:
        db.session.rollback()

        print("\nNo fue posible conectar con la base de datos.", flush=True)
        print(
            "Revisa DATABASE_URL. Si no la defines, el sistema usa SQLite automáticamente.",
            flush=True
        )
        print(f"Detalle técnico: {error.orig}", flush=True)

        raise SystemExit(1) from error

    except SQLAlchemyError as error:
        db.session.rollback()

        print("\nOcurrió un error al preparar la base de datos.", flush=True)
        print(f"Detalle técnico: {error}", flush=True)

        raise SystemExit(1) from error

    finally:
        db.session.remove()

# También prepara la base al iniciar con Gunicorn/Render.
with app.app_context():
    inicializar_base_datos()

if __name__ == "__main__":
    print("Iniciando Cafetería La Curva en http://127.0.0.1:5000")
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "5000")), debug=os.getenv("FLASK_DEBUG") == "1")
