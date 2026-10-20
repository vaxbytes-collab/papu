# Papu 🐈

Bot modular de Discord para PapuCollective: moderacion segura, comunidad, organizacion, minijuegos y mascota virtual persistente, con un sistema visual compartido.

## Modulos

- `main.py`: inicio, Groq chat y sincronizacion global de comandos slash.
- `moderacion.py`: logs, moderacion, sanciones manuales, advertencias y alertas de IA.
- `seguridad.py`: protecciones configurables, filtros de mensajes, alertas de raid, reportes privados y auditoria de permisos.
- `utilidades.py`: recordatorios, encuestas, eventos, sugerencias, sorteos e informacion del servidor.
- `juegos.py`: minijuegos y mascota virtual con monedas, comida, energia y felicidad.
- `papu_store.py`: almacenamiento PostgreSQL con respaldo local JSON y migracion segura.
- `papu_ui.py`: paleta, embeds con marca, mensajes de estado y componentes visuales compartidos.
- `tests/`: pruebas unitarias del almacenamiento.

## Requisitos y ejecucion

Python 3.10+ recomendado. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

Configura las variables de entorno (por ejemplo, en un archivo `.env` local que NO subas a Git):

- `DISCORD_TOKEN`: token del bot.
- `GROQ_API_KEY`: opcional; habilita chat y analisis de moderacion IA.
- `GROQ_CHAT_MODEL`: modelo conversacional opcional.
- `GROQ_MODERATION_MODEL`: modelo clasificador opcional.
- `DATABASE_URL`: URL de conexión PostgreSQL. Cuando se configura, todos los datos persistentes se guardan en la base de datos.
- `PAPU_DATA_DIR`: directorio donde se guardan los JSON. En local, por defecto es `data/`; en Render, por defecto es `/var/data`.
- `PORT`: puerto del endpoint de estado (por defecto 8080).

En Discord Developer Portal activa **Message Content Intent** y **Server Members Intent** cuando uses sus eventos. Invita el bot con permisos minimos necesarios para los modulos activados: ver canales, enviar mensajes, embeds, leer historial, añadir reacciones y los permisos de moderacion que decidas utilizar.

Ejecuta:

```bash
python main.py
```

Los comandos slash se sincronizan al iniciar. Discord puede tardar en mostrar los comandos globales. No despliegues una rama de desarrollo en un servidor principal sin probarla primero.

## Personalidad y formato del chat de Papu

- Papu es un michi grasoso y basado de Sonora, la IA oficial de PapuCollective.
- Sus mensajes salen en minusculas y sin acentos vocalicos; conserva la letra ñ.
- Usa modismos sonorenses y humor clasico de la grasa con moderacion, sin forzar chistes.
- El tono debe sentirse calido y conversacional, no como un contestador automatico: reconoce el comentario de la persona, reacciona con personalidad y pregunta algo de seguimiento cuando ayude.
- Las minúsculas y la ausencia de acentos son solo reglas de formato; no significan que Papu deba ser cortante ni responder siempre con una sola frase.
- Si una persona se queja de que Papu es seco, Papu reconoce el tono y responde con una disculpa juguetona y mas cercana.
- Si llegan adjuntos, Papu explica con amabilidad que la integracion actual no puede analizarlos directamente y ofrece revisar una descripcion o texto copiado.
- Responde en espanol latinoamericano por defecto. Un numero o emoji no indica que el usuario quiera hablar ingles.
- Si el mensaje contiene solo un numero, solo se interpreta como seleccion si el mensaje inmediatamente anterior pidio escoger una opcion numerada; de lo contrario, pregunta que quiso decir.
- Si recibe solo emojis, responde en tono ligero sin atribuir emociones ni inventar que le pasa a la persona.
- No inventa tracklists, titulos, fechas ni datos musicales y no llama "oficial" a listas de las que no tiene certeza.
- Si el primer mensaje es ambiguo (por ejemplo, `1.`), pregunta en espanol sin llamar a la IA. Si le preguntan por que habla ingles, reconoce el error y se disculpa.
- Puede usar carrilla ligera si una persona insiste con una accion que no puede ejecutar por chat, pero nunca acosa ni ataca identidades.
- No ejecuta baneos, muteos ni menciones masivas desde el chat. Las acciones de moderacion deben usar comandos de Discord con los permisos correspondientes.
- La memoria conversacional se limita al contexto por usuario y servidor que el bot tiene disponible; no debe inventar recuerdos ni revelar mensajes de otros miembros.
- El chat tiene un tiempo de espera para que los fallos del proveedor no dejen la conversacion esperando indefinidamente.

## Busqueda web desde el chat

- Papu busca automaticamente cuando le preguntan por tracklists/listas de canciones y otras consultas factuales conocidas, y cuando alguien escribe comandos como `busca`, `buscala`, `investiga` o `averigua`.
- Si el comando es solo `busca`, usa los mensajes previos del usuario para reconstruir el tema.
- La busqueda consulta **Google primero** y, si falla o devuelve cero resultados, prueba por separado Brave, Bing y DuckDuckGo. Separar las consultas evita que un fallo de Google haga que se pierdan resultados de los otros motores. Se usa la region `es-es` para priorizar resultados de Espana.
- Los resultados de búsqueda se pasan al modelo como datos externos no confiables; la respuesta debe enlazar las fuentes exactas y no inventar detalles.
- Si no aparecen resultados, Papu explica que la busqueda fallo en vez de fabricar una respuesta.
- La busqueda necesita acceso a internet desde el alojamiento. No requiere otra API key, pero los motores pueden aplicar limites o bloquear peticiones.
- Los temas de busqueda se envian a proveedores externos. Cuando alguien escribe solo `busca`, Papu reutiliza unicamente el tema factual reciente y aclaraciones cortas (como año o edicion), no conversaciones personales sin relacion.
- Si no hay clave de Groq pero la busqueda funciona, Papu muestra los resultados con enlaces directos.

## Comandos destacados

### Organizacion y comunidad
- `/recordatorio minutos texto`: recordatorio persistente, de 1 minuto a 30 dias.
- `/encuesta pregunta opcion_a opcion_b [opcion_c] [opcion_d]`: encuesta con reacciones.
- `/evento_crear nombre fecha detalles`: evento futuro; fecha ISO 8601 con zona horaria recomendada.
- `/eventos`: agenda guardada.
- `/canal_sugerencias canal`: configura el canal de sugerencias.
- `/sugerencia texto`: publica una propuesta.
- `/sorteo participantes`: sorteo entre menciones; requiere permiso de gestion del servidor.
- `/config_papu`: muestra configuracion comunitaria.
- `/afk [motivo]`: estado AFK persistente; avisa al mencionar a alguien ausente y lo limpia al volver.
- `/rolinfo rol`: detalles de un rol. `/timestamp unix`: convierte un Unix timestamp a formatos de Discord.

### Administracion y moderacion
- `/setlogchannel`, `/logconfig`: registros del servidor.
- `/aimoderacion activar`: activa alertas y acciones en vivo de alta severidad; `/aimoderacion desactivar` las apaga. `/modcheck texto` analiza manualmente sin sancionar.
- `/canal_chat [canal]`: canal optativo donde Papu responde sin mencion; omitir el canal desactiva esa funcion.
- `/warn`, `/warns`, `/unwarn`, `/clearwarns`, `/diagnostico`, `/kick`, `/ban`, `/unban`, `/timeout`, `/untimeout`, `/timeout_estado`, `/purge`, `/purge_usuario`, `/purge_bots`, `/slowmode`, `/lock`, `/unlock`, `/apodo`, `/rol_dar`, `/rol_quitar`.
- `/userinfo`, `/serverinfo`, `/ping`.

### Protecciones automaticas (opt-in)
- `/antispam activar limite ventana timeout_segundos`: borra el mensaje que dispara el limite y aplica timeout configurable. Desactivado por defecto; el caso se registra con la ficha estructurada de moderacion.
- `/antiraid activar umbral ventana`: alerta al canal de logs ante picos de entradas; no banea ni expulsa automaticamente.
- `/antienlaces activar`: bloquea invitaciones de Discord y una lista limitada de dominios conocidos de phishing/rastreo; no bloquea enlaces normales por defecto. Las acciones de este filtro, anti-spam, palabras, menciones, mayusculas y repeticion generan fichas de caso con enlace al mensaje cuando existe. Si no hay un canal de logs operativo, no se aplica la accion automática.
- `/antimenciones activar maximo`: elimina mensajes que superen el limite de menciones.
- `/antirepeticion activar repeticiones ventana`: detecta mensajes repetidos.
- `/filtro_caps activar porcentaje minimo_letras`: filtra mensajes largos con demasiadas mayusculas.
- `/palabra_bloquear palabra`, `/palabra_permitir palabra`, `/palabras_bloqueadas`: gestiona el filtro de palabras/frases por servidor.
- `/canal_reportes canal`, `/reportar usuario motivo`: configura reportes privados para que los revise el staff.
- `/auditoria_permisos`: avisa si @everyone tiene permisos delicados y revisa permisos comunes que le falten al bot.
- `/seguridad_estado`: revisa el estado de todas las protecciones. Usa `/setlogchannel` para recibir alertas.

### Entretenimiento, minijuegos y mascota
- `/momo`, `/chiste`, `/avatar usuario`, `/dilema`, `/frase_michi`.
- `/ppt`, `/dado`, `/moneda`, `/8ball`, `/trivia`.
- `/arcade adivinanza`, `/arcade dado_personalizado caras`, `/arcade dato_michi`, `/arcade reto_sano`, `/arcade palabra_aleatoria`, `/arcade duelo`, `/arcade completa_frase`.
- `/michi_adoptar [nombre]`, `/michi`, `/michi_cuidar`, `/michi_comida`, `/michi_jugar`.

## Identidad visual de Papu

Los comandos que muestran tarjetas usan `papu_ui.py` para mantener una paleta consistente, pies de página de PapuCollective, marcas de tiempo y mensajes de estado. El panel de Michi usa barras visuales para hambre, energía y felicidad; seguridad y moderación comparten el mismo estilo de embeds. Las respuestas conversacionales de la IA siguen siendo mensajes normales para que el chat no se convierta en una sucesión de tarjetas.

## Persistencia

Papu usa **PostgreSQL externo** si existe la variable `DATABASE_URL`; si no, usa JSON local para desarrollo. Todos los módulos utilizan el mismo almacenamiento: michis, recordatorios, eventos, sugerencias, avisos de moderación, configuraciones por servidor y los últimos 13 mensajes de conversación por usuario y servidor. El esquema se crea automáticamente al arrancar.

### Conectar la base de datos en Render

1. Crea una base de datos PostgreSQL en un proveedor compatible (por ejemplo, [Neon](https://neon.com/)).
2. Copia su URL de conexión. Si el proveedor ofrece una conexión agrupada/pooler, úsala para el bot; conserva los parámetros SSL que entregue el proveedor.
3. En Render, abre el servicio **papu** → **Environment** → añade `DATABASE_URL` con la URL. No la escribas en el repositorio ni la compartas en Discord.
4. Guarda la variable y deja que Render despliegue. Al arrancar, Papu comprueba la conexión y crea la tabla `papu_json_store`; si la base de datos falla, no cambia silenciosamente al almacenamiento local, porque eso podría crear una instancia con datos aparentemente vacíos.

La primera inicialización intenta importar los JSON que todavía existan en la raíz, en `data/` o en `/var/data`. La importación no reemplaza datos ya existentes en PostgreSQL. Si Render ya borró los JSON anteriores, no se pueden recuperar desde el código: será necesario restaurar una copia de seguridad para recuperarlos. Si no se configura `DATABASE_URL`, Render sigue necesitando un Persistent Disk en `/var/data` para conservar archivos entre despliegues.

## Seguridad, permisos y privacidad

- **La moderacion IA ya no funciona en modo de prueba cuando activas `/aimoderacion activar`.** Registra casos con usuario, canal, categoria, gravedad, confianza, motivo, mensaje, estado, enlace e ID de infraccion. Solo si la IA marca gravedad 3, confianza de al menos 95% y categoria `sexual`, `threat`, `hate` o `harassment`, intenta borrar el mensaje y aplicar timeout de 24 horas. Los demas casos solo quedan registrados para revision humana; nunca banea ni expulsa automaticamente.
- Al activar `/aimoderacion`, los mensajes analizados se envian a Groq y la moderacion de alta severidad queda en vivo. Informa a los miembros, revisa las condiciones de privacidad aplicables y da a Papu los permisos `Gestionar mensajes` y `Moderar miembros`. Los casos aparecen en el canal configurado mediante `/setlogchannel`.
- Configura `/setlogchannel` hacia un canal privado para el staff antes de activar `/aimoderacion activar`. Ese comando exige que Papu pueda escribir en los logs y que tenga `Gestionar mensajes` y `Moderar miembros`; si faltan, la moderacion en vivo no se activa. Los logs pueden contener mensajes eliminados/editados y datos sensibles.
- El canal de respuesta automatica es opt-in por servidor y se configura con `/canal_chat`. Los mensajes de ese canal tambien pueden enviarse a Groq para generar respuestas.
- Nunca pongas tokens o claves API en el repositorio. Si se filtran, revocalos y genera otros.
- Con `DATABASE_URL`, el historial breve de chat tambien se guarda en PostgreSQL; informa a los miembros de ese almacenamiento y restringe el acceso a la base de datos.
- Da al bot solo los permisos necesarios. Los comandos de moderacion tienen checks de permisos de Discord; el rol del bot debe estar por encima de los miembros a moderar.
- Las protecciones anti-spam, anti-raid y anti-invitaciones empiezan desactivadas y requieren que un administrador las active. Anti-raid solo alerta; no expulsa ni banea automaticamente.
- Los retos de `/arcade reto_sano` son optativos y no deben usarse para acosar, saturar canales o pinguear a todo el servidor.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

El workflow de GitHub Actions ejecuta estas pruebas en cada push y pull request, incluyendo almacenamiento PostgreSQL simulado, migracion JSON y deteccion de enlaces. Todavia hace falta probar interacciones reales y permisos en un servidor privado antes de un despliegue de produccion.
