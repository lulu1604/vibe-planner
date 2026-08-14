"""
VibePlanner v2 - Idiomas (i18n.py)
-----------------------------------
DUENO DE ESTE ARCHIVO: Piero Calderon (Modulo A - Nucleo)

Castellano e ingles, sin dependencias nuevas.

POR QUE NO SE USA Flask-Babel
    Es la herramienta canonica, pero `requirements.txt` tiene UNA linea y la
    regla del equipo es que anadir otra necesita acuerdo del grupo. Babel
    ademas arrastra un flujo de .po/.mo y un paso de compilacion que no
    queremos el dia de la presentacion. Con 200 cadenas, un diccionario en
    memoria hace el mismo trabajo y se lee entero de una sentada.

LA DECISION QUE LO HACE MANEJABLE: LA CLAVE ES EL TEXTO EN CASTELLANO

    t("Mi perfil")   ->  "My profile"  en ingles
                     ->  "Mi perfil"   en castellano, y si falta la traduccion

    En vez de inventar claves tipo `menu.perfil`, la clave ES la frase. Tres
    ventajas concretas:

    1. Si una traduccion falta, sale el castellano. Con claves inventadas
       saldria `menu.perfil` en mitad de la pantalla, que es peor que no
       haber traducido nada.
    2. La plantilla se sigue leyendo: `{{ t("Mi perfil") }}` dice lo que
       pinta. `{{ t("menu.perfil") }}` obliga a ir al diccionario para saberlo.
    3. El cambio en las plantillas es envolver, no reescribir: menos
       superficie para romper algo.

    El precio es que cambiar el castellano rompe el enlace con su traduccion.
    A cambio, el sintoma es que sale en castellano, no un error.

DONDE VIVE EL IDIOMA
    En la sesion, no en localStorage. Los mensajes de `flash()` los genera el
    SERVIDOR, asi que si el idioma viviera solo en el navegador saldrian
    siempre en castellano y tendriamos media pantalla en cada lengua.
"""

from flask import g, has_request_context, session

IDIOMA_POR_DEFECTO = "es"

# Lista blanca. El idioma llega de un formulario y acaba en `<html lang>`.
IDIOMAS = {
    "es": "Espanol",
    "en": "English",
}

SESSION_KEY = "idioma"


# --------------------------------------------------------------------------
# El diccionario
#
# Solo el ingles: el castellano es la clave. Agrupado por pantalla para que
# se pueda revisar, no por orden alfabetico.
# --------------------------------------------------------------------------
TRADUCCIONES = {
    "en": {
        # --- Navegacion y shell ------------------------------------------
        "Planner": "Planner",
        "Tablero": "Board",
        "Calendario": "Calendar",
        "Habitos": "Habits",
        "Metricas": "Metrics",
        "Equipo": "Team",
        "Administracion": "Administration",
        "Metricas del sistema": "System metrics",
        "Mi perfil": "My profile",
        "Gestion de usuarios": "User management",
        "Cerrar sesion": "Sign out",
        "Apariencia": "Appearance",
        "Saltar al contenido": "Skip to content",
        "Volver al inicio": "Back to home",
        "Proximamente": "Coming soon",
        "Entrar": "Sign in",
        "Abrir el menu de tu cuenta": "Open your account menu",
        "Menu principal": "Main menu",

        # --- Acciones comunes --------------------------------------------
        "Guardar cambios": "Save changes",
        "Cancelar": "Cancel",
        "Cerrar": "Close",
        "Listo": "Done",
        "Buscar": "Search",
        "Volver": "Back",
        "Guardando...": "Saving...",
        "Creando...": "Creating...",
        "Entrando...": "Signing in...",
        "Eliminando...": "Deleting...",
        "Aceptando...": "Accepting...",

        # --- Autenticacion -----------------------------------------------
        "Iniciar sesion": "Sign in",
        "Crear cuenta": "Create account",
        "Nombre de usuario": "Username",
        "Contrasena": "Password",
        "Contrasena actual": "Current password",
        "Contrasena nueva": "New password",
        "Cambiar contrasena": "Change password",
        "Correo electronico": "Email address",
        "Nombre completo (opcional)": "Full name (optional)",
        "Nombre completo": "Full name",

        # --- Apariencia ---------------------------------------------------
        "Tema de color": "Colour theme",
        "Idioma": "Language",
        "Claro": "Light",
        "Oscuro": "Dark",
        "Alto contraste": "High contrast",
        "Volver al tema claro": "Back to the light theme",

        # --- Perfil --------------------------------------------------------
        "Tus datos": "Your details",
        "Tus roles y permisos": "Your roles and permissions",
        "Usuario": "User",
        "Administrador": "Administrator",

        # --- Administracion -------------------------------------------------
        "Nueva cuenta": "New account",
        "Cuentas del sistema": "System accounts",
        "Estado": "Status",
        "Roles": "Roles",
        "Acciones": "Actions",
        "Gestionar": "Manage",
        "Activa": "Active",
        "Desactivada": "Deactivated",
        "Desactivar": "Deactivate",
        "Reactivar": "Reactivate",
        "Restablecer contrasena": "Reset password",

        # --- Planner y tablero ---------------------------------------------
        "Nueva actividad": "New activity",
        "Titulo": "Title",
        "Categoria": "Category",
        "Prioridad": "Priority",
        "Alta": "High",
        "Media": "Medium",
        "Baja": "Low",
        "Fecha limite": "Due date",
        "Duracion estimada": "Estimated duration",
        "Backlog": "Backlog",
        "Por hacer": "To do",
        "En curso": "In progress",
        "Hecho": "Done",
        "Mover": "Move",
        "Eliminar": "Delete",
        "Sin actividades": "No activities",

        # --- Calendario -------------------------------------------------------
        "Nuevo evento": "New event",
        "Editar evento": "Edit event",
        "Hoy": "Today",
        "Lun": "Mon", "Mar": "Tue", "Mie": "Wed", "Jue": "Thu",
        "Vie": "Fri", "Sab": "Sat", "Dom": "Sun",
        "Lunes": "Monday", "Martes": "Tuesday", "Miercoles": "Wednesday",
        "Jueves": "Thursday", "Viernes": "Friday", "Sabado": "Saturday",
        "Domingo": "Sunday",
        "Enero": "January", "Febrero": "February", "Marzo": "March",
        "Abril": "April", "Mayo": "May", "Junio": "June",
        "Julio": "July", "Agosto": "August", "Septiembre": "September",
        "Octubre": "October", "Noviembre": "November", "Diciembre": "December",

        # --- Habitos ------------------------------------------------------------
        "Nuevo habito": "New habit",
        "Mis habitos": "My habits",
        "Nombre del habito": "Habit name",
        "Tipo": "Type",
        "Meta diaria": "Daily goal",
        "Unidad": "Unit",
        "Dieta": "Diet",
        "Ejercicio": "Exercise",
        "Relajacion": "Relaxation",
        "Sueno": "Sleep",
        "General": "General",

        # --- Metricas -------------------------------------------------------------
        "Como me fue": "How my day went",
        "Dia anterior": "Previous day",
        "Dia siguiente": "Next day",



        # --- Mensajes de validacion ya resueltos --------------------
        'El usuario debe tener entre 3 y 20 caracteres.': 'The username must be between 3 and 20 characters.',
        'El correo no puede pasar de 120 caracteres.': 'The email cannot exceed 120 characters.',
        'El nombre completo debe tener entre 2 y 80 caracteres.': 'The full name must be between 2 and 80 characters.',
        'La contrasena debe tener al menos 8 caracteres.': 'The password must be at least 8 characters long.',
        'La contrasena no puede pasar de 128 caracteres.': 'The password cannot exceed 128 characters.',
        'El titulo supera los 120 caracteres.': 'The title exceeds 120 characters.',
        'La duracion no puede superar 480 minutos.': 'The duration cannot exceed 480 minutes.',
        'La descripcion no puede pasar de 500 caracteres.': 'The description cannot exceed 500 characters.',
        'La hora de inicio no es valida. Usa el formato HH:MM.': 'The start time is not valid. Use the HH:MM format.',
        'La hora de fin no es valida. Usa el formato HH:MM.': 'The end time is not valid. Use the HH:MM format.',
        'El titulo no puede pasar de 120 caracteres.': 'The title cannot exceed 120 characters.',
        'La fecha u hora de inicio no es valida. Usa el selector del formulario.': 'The start date or time is not valid. Use the form picker.',
        'La fecha u hora de fin no es valida. Usa el selector del formulario.': 'The end date or time is not valid. Use the form picker.',
        'Debes indicar la fecha u hora de inicio.': 'You must provide the start date or time.',
        'Debes indicar la fecha u hora de fin.': 'You must provide the end date or time.',
        'Entre 3 y 20 caracteres. Letras, numeros, punto y guion bajo.': 'Between 3 and 20 characters. Letters, numbers, dots and underscores.',
        'Lo usaras para entrar y para recuperar tu cuenta.': 'You will use it to sign in and to recover your account.',
        'Como quieres que te llamemos en la aplicacion.': 'How you want us to address you in the app.',
        'Minimo 8 caracteres. Se guarda cifrada.': 'At least 8 characters. Stored encrypted.',
        # --- Mensajes del servidor (flash y validaciones) ----------
        'Escribe un nombre de usuario.': 'Enter a username.',
        'El usuario debe tener entre {min} y {max} caracteres.': 'The username must be between {min} and {max} characters.',
        'El usuario solo puede llevar letras, numeros, punto y guion bajo, y debe empezar por una letra.': 'The username may only contain letters, numbers, dots and underscores, and must start with a letter.',
        'Escribe tu correo.': 'Enter your email.',
        'El correo no puede pasar de {max} caracteres.': 'The email cannot exceed {max} characters.',
        'Escribe un correo valido, por ejemplo nombre@dominio.com.': 'Enter a valid email, for example name@domain.com.',
        'El nombre completo debe tener entre {min} y {max} caracteres.': 'The full name must be between {min} and {max} characters.',
        'Escribe una contrasena.': 'Enter a password.',
        'La contrasena debe tener al menos {min} caracteres.': 'The password must be at least {min} characters long.',
        'La contrasena no puede pasar de {max} caracteres.': 'The password cannot exceed {max} characters.',
        'Esa contrasena es demasiado facil de adivinar. Elige otra.': 'That password is too easy to guess. Choose another one.',
        'La contrasena no puede ser igual a tu usuario ni a tu correo.': 'The password cannot be the same as your username or your email.',
        'Ese usuario o correo ya esta registrado.': 'That username or email is already registered.',
        'Usuario o contrasena incorrectos.': 'Wrong username or password.',
        'Tu cuenta esta desactivada. Contacta al administrador.': 'Your account is deactivated. Contact an administrator.',
        'Ese nombre de usuario ya esta en uso.': 'That username is already in use.',
        'Ese correo ya esta registrado en otra cuenta.': 'That email is already registered to another account.',
        'No se pudo crear la cuenta.': 'The account could not be created.',
        'Tus datos quedaron actualizados.': 'Your details were updated.',
        'Tu contrasena quedo actualizada.': 'Your password was updated.',
        'Tu contrasena actual no es correcta.': 'Your current password is not correct.',
        'La contrasena nueva tiene que ser distinta de la actual.': 'The new password must be different from the current one.',
        'Evento creado.': 'Event created.',
        'Evento actualizado.': 'Event updated.',
        'Evento eliminado.': 'Event deleted.',
        'No se pudo eliminar el evento.': 'The event could not be deleted.',
        'La invitacion no es valida.': 'The invitation is not valid.',
        'El titulo del evento es obligatorio.': 'The event title is required.',
        'La hora de fin debe ser posterior a la de inicio.': 'The end time must be later than the start time.',
        'Actividad creada.': 'Activity created.',
        'Actividad actualizada.': 'Activity updated.',
        'Actividad eliminada.': 'Activity deleted.',
        'El titulo no puede estar vacio.': 'The title cannot be empty.',
        'La fecha limite es obligatoria.': 'The due date is required.',
        'La fecha debe tener formato AAAA-MM-DD.': 'The date must use the YYYY-MM-DD format.',
        'La duracion debe ser mayor a 0 minutos.': 'The duration must be greater than 0 minutes.',
        'La prioridad debe ser Alta (1), Media (2) o Baja (3).': 'The priority must be High (1), Medium (2) or Low (3).',
        'Esa columna del tablero no existe.': 'That board column does not exist.',
        'No puedes asignar actividades a otras personas.': 'You cannot assign activities to other people.',
        'Esa cuenta no existe o esta desactivada.': 'That account does not exist or is deactivated.',
        'Habito creado.': 'Habit created.',
        'Marcado de hoy actualizado.': "Today's mark updated.",
        'Registro de hoy desmarcado.': "Today's entry unmarked.",
        'El valor del dia debe ser un numero. Por ejemplo: 8.': 'The daily value must be a number. For example: 8.',
        # --- Volcado de las pantallas -------------------------------
        'Tu plan del dia, ordenado y explicado.': 'Your day, sorted and explained.',
        'Entraste como': 'Signed in as',
        'Abrir': 'Open',
        'Aun no disponible': 'Not available yet',
        'Proximamente: este modulo aun se esta construyendo': 'Coming soon: this module is still being built',
        'Tu cuenta aun no tiene modulos asignados': 'Your account has no modules yet',
        'Pidele a un administrador que revise tus permisos.': 'Ask an administrator to review your permissions.',
        'El tema se aplica al instante y se recuerda en este navegador.': 'The theme applies instantly and is remembered in this browser.',
        'El de siempre: fondo beige y barra lateral azul noche.': 'The usual one: beige background and navy sidebar.',
        'Descansa la vista de noche. Contraste verificado, no solo invertido.': 'Easier on the eyes at night. Contrast verified, not just inverted.',
        'Negro sobre blanco y bordes gruesos, para cuando el color no basta.': 'Black on white with thick borders, for when colour is not enough.',
        'Cancelar': 'Cancel',
        'es tu cuenta': 'this is your account',
        'Volver al listado': 'Back to the list',
        'Datos de la cuenta': 'Account details',
        'No se puede cambiar: es la identidad con la que entra y con la que la ven los demas.': 'Cannot be changed: it is the identity they sign in with and how others see them.',
        'Guardar datos': 'Save details',
        'Correo': 'Email',
        'Los permisos son la': 'Permissions are the',
        'suma': 'sum',
        'Esta es tu cuenta. Si te quitas Administrador y eres el ultimo, el sistema no te dejara.': 'This is your account. If you remove Administrator and you are the last one, the system will stop you.',
        'Guardar roles': 'Save roles',
        'Nueva contrasena': 'New password',
        'Estado de la cuenta': 'Account status',
        'No puedes desactivar tu propia cuenta. Pideselo a otro administrador.': 'You cannot deactivate your own account. Ask another administrator.',
        'La cuenta esta': 'The account is',
        'activa': 'active',
        'desactivada': 'deactivated',
        'sus tareas y eventos no se borran': 'their tasks and events are not deleted',
        'y puedes reactivarla cuando quieras.': 'and you can reactivate it whenever you want.',
        'Desactivar cuenta': 'Deactivate account',
        'Reactivar cuenta': 'Reactivate account',
        'Permisos efectivos': 'Effective permissions',
        'Ver la lista completa': 'See the full list',
        'No podra iniciar sesion mientras este desactivada.': 'They will not be able to sign in while deactivated.',
        'Sus tareas y eventos no se borran': 'Their tasks and events are not deleted',
        'y puedes reactivarla cuando quieras desde esta misma pantalla.': 'and you can reactivate it from this same screen whenever you want.',
        'Buscar cuenta': 'Search account',
        'Quitar filtro': 'Clear filter',
        'Cuentas del sistema con sus roles, su estado y las acciones disponibles': 'System accounts with their roles, status and available actions',
        'Nombre': 'Name',
        'Anterior': 'Previous',
        'Siguiente': 'Next',
        'Sin resultados': 'No results',
        'Aun no hay mas cuentas que la tuya': 'There are no accounts other than yours yet',
        'Crea la primera con el boton «Nueva cuenta» de arriba.': 'Create the first one with the New account button above.',
        'Crear una cuenta': 'Create an account',
        'Ese usuario o correo ya esta registrado.': 'That username or email is already registered.',
        'Quieres iniciar sesion?': 'Want to sign in?',
        'Volver al calendario': 'Back to the calendar',
        'Titulo del evento': 'Event title',
        'Descripcion': 'Description',
        'Fecha de inicio': 'Start date',
        'Hora de inicio': 'Start time',
        'Fecha de fin': 'End date',
        'Hora de fin': 'End time',
        'Tiene que ser posterior a la hora de inicio.': 'It must be later than the start time.',
        'Color del evento': 'Event colour',
        'Invitar a este evento': 'Invite to this event',
        'Generar link de invitacion': 'Generate invitation link',
        'Eliminar evento': 'Delete event',
        'Se borra para ti y para quienes aceptaron la invitacion. No se puede deshacer.': 'It is deleted for you and for everyone who accepted. This cannot be undone.',
        'Desaparecera de tu calendario y del de quienes aceptaron la invitacion.': 'It will disappear from your calendar and from those who accepted the invitation.',
        'Esta accion no se puede deshacer.': 'This action cannot be undone.',
        'Puede que el link este mal copiado o que quien te invito haya cancelado la invitacion. Pidesela de nuevo.': 'The link may be mistyped, or whoever invited you may have cancelled it. Ask them again.',
        'Ir a mi calendario': 'Go to my calendar',
        'Te invita': 'Invited by',
        'Empieza': 'Starts',
        'Termina': 'Ends',
        'Ya confirmaron': 'Already confirmed',
        'Detalles': 'Details',
        'Aceptar y agregar a mi calendario': 'Accept and add to my calendar',
        'Aceptar dos veces no pasa nada: solo se guarda una.': 'Accepting twice is harmless: only one is saved.',
        'Tus eventos y aquellos a los que aceptaste una invitacion.': 'Your events and those you accepted an invitation to.',
        'Mes anterior:': 'Previous month:',
        'Mes siguiente:': 'Next month:',
        'Sin eventos este mes': 'No events this month',
        'Crea el primero y aparecera en su dia.': 'Create the first one and it will show on its day.',
        'Por que este orden?': 'Why this order?',
        'Entendido': 'Got it',
        'Volver atras': 'Go back',
        'Puede que el enlace este mal escrito, o que eso que buscas ya no exista.': 'The link may be mistyped, or what you are looking for may no longer exist.',
        'No fue culpa tuya. El error quedo registrado y tus datos no se han perdido: lo ultimo que guardaste sigue ahi.': 'It was not your fault. The error was logged and your data is safe: whatever you saved last is still there.',
        'Marcado hoy': 'Marked today',
        'Sin marcar': 'Not marked',
        'Empieza hoy': 'Start today',
        'día seguido': 'day in a row',
        'días seguidos': 'days in a row',
        'Guardar': 'Save',
        'Desmarcar': 'Unmark',
        'Marcar hoy': 'Mark today',
        'Tus rachas de sueño, ejercicio y alimentación.': 'Your sleep, exercise and diet streaks.',
        'Nuevo hábito': 'New habit',
        'Aún no sigues ningún hábito': 'You are not tracking any habit yet',
        'Empieza por uno: dormir, ejercicio o alimentación.': 'Start with one: sleep, exercise or diet.',
        'Crear el primero': 'Create the first one',
        'Cuánto cuenta como cumplido. Por ejemplo: 8.': 'How much counts as done. For example: 8.',
        'Crear hábito': 'Create habit',
        'Empezar un hábito': 'Start a habit',
        'Día siguiente →': 'Next day →',
        'Actividades completadas': 'activities completed',
        'Hábitos de hoy:': 'Today habits:',
        'Ver mis hábitos': 'See my habits',
        'Eventos del día:': 'Events today:',
        'Ver el calendario': 'See the calendar',
        'Sin actividad este día': 'No activity that day',
        'Hoy no registraste actividad. Cuando completes algo, lo verás aquí.': 'You did not record any activity today. When you complete something, it will show here.',
        'Cuánto se usa VibePlanner. Solo cifras agregadas.': 'How much VibePlanner is used. Aggregate figures only.',
        'Cuentas': 'Accounts',
        'Cuentas registradas': 'Registered accounts',
        'Todas las cuentas, activas o no.': 'All accounts, active or not.',
        'Cuentas activas': 'Active accounts',
        'Pueden iniciar sesión ahora mismo.': 'Can sign in right now.',
        'Eventos creados': 'Events created',
        'En todo el histórico.': 'Across all history.',
        'Hábitos activos': 'Active habits',
        'Rutinas que la gente sigue.': 'Routines people follow.',
        'Usaron la app hoy': 'Used the app today',
        'Personas distintas con actividad hoy.': 'Distinct people with activity today.',
        'El nombre de usuario no se puede cambiar. Si necesitas otro, pideselo a un administrador.': 'The username cannot be changed. If you need a different one, ask an administrator.',
        'Contrasena nueva': 'New password',
        'Tus permisos son la': 'Your permissions are the',
        'de todos tus roles. Aqui puedes ver exactamente que te permite hacer el sistema y por que.': 'of all your roles. Here you can see exactly what the system lets you do, and why.',
        'Avance de hoy': "Today's progress",
        'El backlog no cuenta: solo las tareas comprometidas para hoy.': 'The backlog does not count: only tasks committed for today.',
        'Tiempo disponible hoy': 'Time available today',
        'Minutos. Las actividades que entren en ese hueco suman +15 pts.': 'Minutes. Activities that fit in that slot add +15 pts.',
        'Actualizar': 'Update',
        'Hoy no tienes nada planeado': 'You have nothing planned today',
        'Agrega tu primera actividad y verás tu día ordenado por importancia.': 'Add your first activity and you will see your day sorted by importance.',
        'Asignada por otro usuario': 'Assigned by another user',
        '¿Por qué?': 'Why?',
        'Título': 'Title',
        'Descripción (opcional)': 'Description (optional)',
        'Categoría': 'Category',
        'Fecha límite': 'Due date',
        'Duración (min)': 'Duration (min)',
        'Hora inicio (opcional)': 'Start time (optional)',
        'Hora fin (opcional)': 'End time (optional)',
        'Columna inicial': 'Initial column',
        'Asignar a compañero (opcional)': 'Assign to a teammate (optional)',
        'Para mí (Sin asignar)': 'For me (unassigned)',
        'Agregar actividad': 'Add activity',
        'Actividades que asignaste a otros integrantes.': 'Activities you assigned to other members.',
        'Aún no has asignado actividades': 'You have not assigned any activities yet',
        'Cuando crees una tarea y la asignes a otro usuario, aparecerá aquí agrupada por persona.': 'When you create a task and assign it to another user, it will appear here grouped by person.',
        'Ir al planner': 'Go to the planner',
        'pendientes de': 'pending out of',
        'tareas asignadas a': 'tasks assigned to',
        'Arrastra las tarjetas entre columnas o usa los botones.': 'Drag the cards between columns or use the buttons.',
        'Asignada': 'Assigned',
    },
}


# --------------------------------------------------------------------------
# API
# --------------------------------------------------------------------------
def idioma_actual():
    """
    El idioma de esta peticion.

    Se cachea en `g` -- dura UNA peticion -- porque una pantalla llama a t()
    cientos de veces y no tiene sentido volver a mirar la sesion cada vez.
    """
    if not has_request_context():
        return IDIOMA_POR_DEFECTO

    if "idioma" not in g:
        elegido = session.get(SESSION_KEY, IDIOMA_POR_DEFECTO)
        # Lista blanca: esto acaba en el atributo `lang` del <html>.
        g.idioma = elegido if elegido in IDIOMAS else IDIOMA_POR_DEFECTO
    return g.idioma


def t(texto, **variables):
    """
    Traduce `texto` al idioma de la peticion.

    Si no hay traduccion devuelve el castellano tal cual, que es la razon de
    que la clave sea la propia frase: una traduccion olvidada se ve como una
    frase en castellano, no como un `menu.perfil` suelto en la pantalla.

    Acepta variables con formato de llaves:
        t("Cuenta {usuario} creada.", usuario="ana")
    """
    idioma = idioma_actual()
    salida = TRADUCCIONES.get(idioma, {}).get(texto, texto)
    if variables:
        try:
            salida = salida.format(**variables)
        except (KeyError, IndexError):
            # Una traduccion con las llaves mal escritas no puede tumbar la
            # pantalla: se devuelve sin sustituir y se ve el hueco.
            pass
    return salida


def fijar_idioma(codigo):
    """Guarda el idioma en la sesion. Devuelve el que quedo puesto."""
    codigo = codigo if codigo in IDIOMAS else IDIOMA_POR_DEFECTO
    session[SESSION_KEY] = codigo
    g.pop("idioma", None)          # invalidar la cache de esta peticion
    return codigo


def init_app(app):
    """
    Expone `t`, `idioma_actual` e `IDIOMAS` a todas las plantillas.

    Lo llama app.py una vez. Sin esto, cada ruta tendria que pasar `t` en su
    render_template y bastaria olvidarlo en una para que esa pantalla
    reventara con "t is undefined".
    """
    app.jinja_env.globals["t"] = t
    app.jinja_env.globals["idioma_actual"] = idioma_actual
    app.jinja_env.globals["IDIOMAS"] = IDIOMAS


# --------------------------------------------------------------------------
# Pruebas: python i18n.py
# --------------------------------------------------------------------------
if __name__ == "__main__":
    # Sin contexto de peticion cae al castellano y no revienta: lo usan los
    # scripts de consola como seed.py.
    assert idioma_actual() == "es"
    assert t("Mi perfil") == "Mi perfil"

    # El diccionario no tiene claves vacias ni traducciones identicas por
    # descuido en palabras que SI cambian.
    en = TRADUCCIONES["en"]
    assert all(k and v for k, v in en.items()), "hay claves o valores vacios"
    assert en["Cerrar sesion"] == "Sign out"
    assert en["Miercoles"] == "Wednesday"

    # Las variables se sustituyen.
    from flask import Flask
    app = Flask(__name__)
    app.secret_key = "test"
    with app.test_request_context():
        session[SESSION_KEY] = "en"
        assert idioma_actual() == "en"
        assert t("Mi perfil") == "My profile"
        assert t("No existe esta frase") == "No existe esta frase", "el respaldo debe ser el castellano"

        # Una traduccion con llaves rotas no puede tumbar la pantalla.
        TRADUCCIONES["en"]["prueba {a}"] = "test {b}"
        assert t("prueba {a}", a=1) == "test {b}"
        del TRADUCCIONES["en"]["prueba {a}"]

    # Un idioma inventado cae al por defecto, no se propaga a <html lang>.
    with app.test_request_context():
        session[SESSION_KEY] = "'><script>"
        assert idioma_actual() == "es"

    print("i18n.py: %d traducciones al ingles, comprobaciones en verde" % len(en))
