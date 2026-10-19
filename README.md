# papu 🐈

Bot de Discord de PapuCollective con comandos slash, moderacion, logs configurables y revision de seguridad asistida por IA.

## Funciones
- Canal de logs configurable por servidor: **/setlogchannel** y **/logconfig**.
- Logs de mensajes editados/eliminados, entradas/salidas, sanciones y alertas de IA.
- Moderacion asistida por IA: **/aimoderacion** activa alertas y **/modcheck** analiza texto manualmente.
- Sanciones con permisos de Discord, limites de duracion/cantidad y comprobaciones de jerarquia.
- Advertencias persistentes con motivo, moderador y fecha.
- Chat con Groq al mencionar al bot, con historial acotado por usuario y servidor.

**Importante:** la IA no borra mensajes ni aplica sanciones automaticamente. Sus resultados requieren revision humana y pueden equivocarse.

## Configuracion
1. Instala Python 3.10 o superior.
2. Instala dependencias con: python -m pip install -r requirements.txt
3. Configura las variables de entorno **DISCORD_TOKEN** y **GROQ_API_KEY**. Opcionales: **GROQ_CHAT_MODEL**, **GROQ_MODERATION_MODEL**, **PAPU_DATA_DIR** y **PORT**.
4. En el Developer Portal de Discord, activa Message Content Intent y Server Members Intent si vas a usar esos eventos.
5. Invita el bot con los permisos que necesita: ver canales, enviar mensajes, embeds, leer historial y los permisos de moderacion que decidas usar.
6. Ejecuta python main.py.
7. Un administrador usa **/setlogchannel** y elige un canal privado de logs.
8. Activa las alertas con **/aimoderacion activar:true**; para apagarlas, usa **/aimoderacion activar:false**.

## Comandos de moderacion
- **/setlogchannel**: configura el canal de registros.
- **/logconfig**: comprueba la configuracion.
- **/aimoderacion**: activa o desactiva alertas de IA.
- **/modcheck**: analiza un texto manualmente.
- **/warn**, **/warns**, **/clearwarns**: gestiona advertencias.
- **/kick**, **/ban**, **/unban**: expulsa, banea o desbanea.
- **/timeout**, **/untimeout**: aplica o retira timeout.
- **/purge**: borra hasta 100 mensajes recientes.
- **/slowmode**, **/lock**, **/unlock**: controla el canal actual.

## Seguridad y privacidad
- Nunca publiques tokens ni claves en el repositorio. Si una clave se filtra, rótala.
- Limita el acceso al canal de logs: puede contener contenido sensible.
- Los mensajes analizados se envian al proveedor de IA configurado (Groq). Informa a la comunidad y revisa las politicas aplicables antes de activar el analisis automatico.
- La IA puede producir falsos positivos o negativos; no uses su puntuacion como prueba definitiva.
- Los JSON son almacenamiento local sencillo. En hostings efimeros, configura PAPU_DATA_DIR en un disco persistente.
- Discord exige que el rol del bot este por encima de los usuarios que modera.

La web de estado usa Flask en el puerto definido por PORT (8080 por defecto).
