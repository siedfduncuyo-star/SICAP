# SICAP

Sistema Integral de Carga y Actualización de la Planificación Docente.

Aplicación web para la carga compartida de programas de Abogacía. Se prepara para desplegar en un servidor Debian 13 detrás de un proxy reverso. GitHub conserva el código; GitHub Pages no aloja esta aplicación porque necesita servidor y base de datos.

## Qué incluye

- Acceso autenticado y bandeja común de programas.
- Asistente de cinco pantallas: identificación y datos de cátedra; contenidos del programa; fechas de trabajos prácticos y parciales; horarios de consulta; revisión final.
- Catálogo de espacios curriculares administrable y datos precargados según la información curricular disponible.
- Guardado central de borradores y envío de programas.
- Descarga de cada programa como PDF con el logo de la Facultad.
- Modo claro y oscuro con preferencia guardada en el navegador.
- Diseño responsive, accesible y basado en la identidad visual indicada para la Agenda de la Facultad: azul institucional, acento dorado `#C5AD68`, fondos claros y oscuros de tonos azulados, controles compactos y tarjetas sobrias.

## Puesta en marcha local

Requisitos: Docker y Docker Compose.

1. Copiar `.env.example` como `.env` y definir contraseñas seguras. Para probar sin HTTPS localmente, usar `DJANGO_DEBUG=1`, `DJANGO_SSL_REDIRECT=0` y `DJANGO_SECURE_COOKIES=0`; en el servidor Debian dejar esos valores de producción.
2. Ejecutar `docker compose up --build -d`.
3. Crear la cuenta administradora con `docker compose exec web python manage.py createsuperuser`.
4. Abrir el dominio o dirección configurada en el proxy y entrar con la cuenta creada.
5. Ingresar a `/admin/` para mantener el catálogo de materias y crear cuentas docentes.

El proxy reverso debe terminar HTTPS y reenviar a `127.0.0.1:8000`. No exponer PostgreSQL a Internet. En `deploy/nginx-proxy.example.conf` hay un fragmento de configuración si el proxy elegido es Nginx.

## Flujo de la carga

1. **Datos de la cátedra:** año académico, carrera, plan, materia, año de cursado, turno cuando corresponde, datos curriculares y equipo docente.
2. **Programa:** encuadre/fundamentación, objetivos, expectativas de logro, metodología, unidades y contenidos, evaluación y bibliografía.
3. **Fechas:** planificación de trabajos prácticos y parciales.
4. **Horarios de consulta:** SICDo se abre dentro del paso para revisar y gestionar los horarios. SICAP registra la confirmación; el portal externo conserva esos datos.
5. **Revisión:** vista completa, guardado/enviado y PDF descargable.

El sistema no usa SICU ni el libro azul. El paso de consultas incrusta SICDo (`https://consultas.derecho.uncu.edu.ar/horarios`) y también ofrece abrirlo en una pestaña nueva si el navegador o el servidor de SICDo impide la incrustación. SICAP guarda la confirmación, mientras que SICDo conserva los horarios. El listado de docentes y asignaturas se mantiene desde el administrador; no se incluyeron direcciones de correo del Excel fuente en el repositorio. Los datos de correlatividades deben cargarse y validarse desde el plan de estudios antes de usarse como definitivos. Los horarios de cursado no se mezclan con los horarios de consulta.

## Seguridad y respaldos

- No subir `.env`, contraseñas, archivos de docentes ni respaldos con datos institucionales al repositorio.
- Crear cuentas docentes desde `/admin/`; no hay autorregistro público.
- Los programas son visibles para los usuarios autenticados. Cada docente puede editar sus borradores; administración puede editar todos.
- Configurar respaldos regulares de PostgreSQL y del directorio `media/`. Probar la restauración antes de usar SICAP en producción.

## Datos curriculares

El catálogo inicial se arma con los espacios y horas que se compartieron para Abogacía. Los turnos de algunas materias se sugieren según la planilla horaria compartida y deben confirmarse para cada ciclo lectivo. Las horas están precargadas como referencia; las correlatividades quedan para completar y validar contra el plan escaneado. Al seleccionar una materia se pueden recuperar algunos campos del programa enviado más reciente de esa misma asignatura. Formato, régimen, carácter, evaluación, carga semanal y créditos se confirman por cátedra y no se copian a todas las materias a partir del ejemplo de PPS VII.

## Estructura

- `config/`: configuración Django.
- `programas/`: modelos, vistas, administración, PDF y carga del catálogo.
- `templates/` y `static/`: interfaz SICAP.
- `deploy/`: ejemplo para el proxy reverso.
- `docker-compose.yml`: aplicación y PostgreSQL.

