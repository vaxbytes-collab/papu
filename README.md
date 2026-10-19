# Papu 🐈

Bot modular de Discord para PapuCollective: moderacion segura, comunidad, organizacion, minijuegos, mascota persistente y musica por voz.

## Modulos

- `main.py`: inicio, Groq chat y sincronizacion global de comandos slash.
- `moderacion.py`: logs, moderacion, advertencias y alertas de IA.
- `utilidades.py`: recordatorios, encuestas, eventos, sugerencias, sorteos e informacion del servidor.
- `juegos.py`: minijuegos y mascota virtual con monedas, comida, energia y felicidad.
- `musica.py`: cola y reproduccion por voz con controles slash.
- `papu_store.py`: persistencia JSON con escritura atomica.
- `tests/`: pruebas unitarias del almacenamiento.

## Requisitos y ejecucion

Python 3.10+ recomendado. Instala dependencias:

```bash
python -m pip install -r requirements.txt
```

La musica por voz requiere **FFmpeg instalado y accesible desde PATH**, ademas de PyNaCl y yt-dlp (incluidos en requirements). El soporte de fuentes externas puede cambiar y debe respetar las condiciones del servicio de origen y los derechos de autor.

Configura las variables de entorno (por ejemplo, en un archivo `.env` local que NO subas a Git):

- `DISCORD_TOKEN`: token del bot.
- `GROQ_API_KEY`: opcional; habilita chat y analisis de moderacion IA.
- `GROQ_CHAT_MODEL`: modelo conversacional opcional.
- `GROQ_MODERATION_MODEL`: modelo clasificador opcional.
- `PAPU_DATA_DIR`: carpeta persistente para JSON (por defecto `data/`).
- `PORT`: puerto del endpoint de estado (por defecto 8080).

En Discord Developer Portal activa **Message Content Intent** y **Server Members Intent** cuando uses sus eventos. Invita el bot con permisos minimos necesarios para los modulos activados: ver canales, enviar mensajes, embeds, leer historial, añadir reacciones y los permisos de moderacion/voz que decidas utilizar.

Ejecuta:

```bash
python main.py
```

Los comandos slash se sincronizan al iniciar. Discord puede tardar en mostrar los comandos globales. No despliegues una rama de desarrollo en un servidor principal sin probarla primero.

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

### Administracion y moderacion
- `/setlogchannel`, `/logconfig`: registros del servidor.
- `/aimoderacion activar`, `/modcheck texto`: alertas de IA y revision manual.
- `/canal_chat [canal]`: canal optativo donde Papu responde sin mencion; omitir el canal desactiva esa funcion.
- `/warn`, `/warns`, `/unwarn`, `/clearwarns`, `/diagnostico`, `/kick`, `/ban`, `/unban`, `/timeout`, `/untimeout`, `/purge`, `/slowmode`, `/lock`, `/unlock`.
- `/userinfo`, `/serverinfo`, `/ping`.

### Minijuegos y mascota
- `/ppt`, `/dado`, `/moneda`, `/8ball`, `/trivia`, `/caos`.
- `/michi_adoptar [nombre]`, `/michi`, `/michi_cuidar`, `/michi_comida`, `/michi_jugar`.\n- Los comandos heredados de entretenimiento usan `/ppt_clasico`, `/dado_clasico`, `/moneda_clasica`, `/bola8_clasica` y `/serverinfo_clasico` para no duplicar nombres.

### Musica
- `/play consulta`, `/cola`, `/pause`, `/resume`, `/skip`, `/stop`.
- Los comandos de audio necesitan FFmpeg y permisos para conectar/hablar. Algunas fuentes pueden dejar de funcionar o bloquear la extraccion.

## Persistencia

Los JSON se guardan en `PAPU_DATA_DIR` (por defecto, la raiz del proyecto para conservar compatibilidad con la configuracion de moderacion existente). Para hosting efimero, monta un disco persistente o los recordatorios, configuracion, sugerencias, eventos y mascotas se perderan al reiniciar. Los ficheros JSON son adecuados para una instancia pequeña; para multiples procesos o alto volumen, migra a SQLite/PostgreSQL y añade transacciones.

## Seguridad, permisos y privacidad

- **La IA nunca sanciona automaticamente.** Clasifica texto y puede generar falsos positivos o negativos; el staff debe revisar el contexto antes de actuar.
- Al activar `/aimoderacion`, los mensajes analizados se envian a Groq. Informa claramente a los miembros antes de activarlo y revisa las condiciones y politicas aplicables.
- Configura `/setlogchannel` hacia un canal privado para el staff. Los logs pueden contener mensajes eliminados/editados y datos sensibles.
- El canal de respuesta automatica es opt-in por servidor y se configura con `/canal_chat`. Los mensajes de ese canal tambien pueden enviarse a Groq para generar respuestas.
- Nunca pongas tokens o claves API en el repositorio. Si se filtran, revocalos y genera otros.
- Da al bot solo los permisos necesarios. Los comandos de moderacion tienen checks de permisos de Discord; el rol del bot debe estar por encima de los miembros a moderar.
- Los minijuegos de caos son optativos y no deben usarse para acosar, saturar canales o pinguear a todo el servidor.

## Pruebas

```bash
python -m unittest discover -s tests -v
```

El workflow de GitHub Actions ejecuta estas pruebas en cada push y pull request. Las pruebas unitarias cubren la persistencia local; todavia hace falta probar interacciones reales en un servidor privado de Discord antes de un despliegue de produccion.
