# Project Management API (Flask + MySQL)
Proyecto ejemplo: sistema de gestión de proyectos y tareas.

Características:
- Flask + SQLAlchemy + Flask-Migrate
- Autenticación JWT
- Roles: admin, manager, viewer
- CRUD para usuarios, proyectos y tareas
- Logs en archivo rotatorio y tabla `logs`
- Dockerfile + docker-compose para desarrollo local
- Listo para deploy en Railway / Render

## Quickstart (local, sin Docker)
1. Copia `.env.example` a `.env` y ajusta variables.
2. Crea entorno y instala dependencias:
   ```
   python -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt
   ```
3. Inicializa migraciones y crea roles/usuario por defecto:
   ```
   flask db init
   flask db migrate -m "initial"
   flask db upgrade
   flask create-defaults
   ```
4. Ejecuta:
   ```
   flask run --host=0.0.0.0 --port=5000
   ```

## Quickstart (Docker Compose)
```
docker-compose up --build
# luego dentro del contenedor:
docker-compose exec web flask db upgrade
docker-compose exec web flask create-defaults
```

## Endpoints importantes (ejemplos)
- POST /api/auth/login  -> {username,password}
- GET  /api/projects
- POST /api/projects
- GET  /api/tasks
- POST /api/tasks

## Deploy
Revisa las instrucciones en el documento principal para Railway y Render (variables de entorno, migraciones, start command).
