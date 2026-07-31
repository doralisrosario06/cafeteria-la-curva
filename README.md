# Cafetería La Curva 2.0

Sistema web instalable (PWA) para ventas, inventario, caja, fiados, clientes, proveedores, compras, gastos, reportes, ganancias, usuarios, permisos, papelera, auditoría y respaldos.

## Uso inmediato en Windows
1. Instala Python 3.11 o superior.
2. Ejecuta `INICIAR_APP.bat`.
3. Abre `http://127.0.0.1:5000`.
4. Usuario inicial: `admin` / contraseña: `1234`.
5. Cambia la contraseña inicial y crea tus empleados.

En modo local usa `cafeteria_la_curva.db`. No borres ese archivo. Descarga respaldos periódicamente desde Configuración.

## Usarlo desde cualquier dispositivo
Para compartir los mismos datos entre celulares, tabletas y computadoras debes publicarlo:

1. Sube esta carpeta a un repositorio privado de GitHub.
2. Crea una base PostgreSQL gratuita en Neon.
3. Crea un servicio web gratuito en Render conectado al repositorio.
4. En Render agrega:
   - `DATABASE_URL`: cadena de conexión de Neon.
   - `SECRET_KEY`: texto largo y secreto.
   - `COOKIE_SECURE`: `1`.
5. Build command: `pip install -r requirements.txt`.
6. Start command: `gunicorn app:app`.

También se incluye `render.yaml` y `Procfile`.

## Instalar como app
Al abrir la URL publicada en Chrome o Edge, selecciona **Instalar aplicación** o **Agregar a pantalla de inicio**. En iPhone: Compartir > Agregar a inicio.

## Datos y seguridad
- Los datos compartidos se guardan en PostgreSQL, no dentro del teléfono.
- Las contraseñas se almacenan cifradas mediante hash.
- Cada usuario tiene permisos por módulo.
- `/salud` permite verificar aplicación y base de datos.
- El modo local ofrece ZIP de respaldo desde Configuración.

## Nota realista sobre planes gratuitos
Los proveedores gratuitos pueden cambiar límites, suspender servicios inactivos o requerir reactivación. Para un negocio que no puede detenerse, conviene pasar a un plan económico cuando el sistema ya esté en uso diario.

## Publicación recomendada: Render + Neon
Esta versión está preparada para usar Render como servidor y Neon como PostgreSQL persistente.

1. Crea una base PostgreSQL en Neon y copia su cadena de conexión.
2. Sube esta carpeta completa a un repositorio de GitHub.
3. En Render selecciona **New > Blueprint** y conecta el repositorio.
4. Render leerá `render.yaml`.
5. Completa las variables solicitadas:
   - `DATABASE_URL`: cadena de Neon, incluyendo `sslmode=require`.
   - `ADMIN_PASSWORD`: contraseña inicial segura.
6. Pulsa **Apply** y espera a que `/salud` indique `database: connected`.

No uses PostgreSQL gratuito de Render para datos permanentes: actualmente esas bases gratuitas vencen después de 30 días. Para mantener los datos en el plan gratuito, usa Neon y realiza snapshots o respaldos periódicos.

## Comprobaciones incluidas
- `python VERIFICAR_PROYECTO.py`: revisa sintaxis básica, archivos obligatorios y enlaces de plantillas.
- `/salud`: comprueba servidor y conexión de base de datos.
- El service worker solo guarda recursos estáticos; no almacena ventas ni páginas privadas.
