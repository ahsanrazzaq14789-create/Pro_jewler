# Gold & Silver Jewellery Management

Full-stack jewellery business management project.

## Project Structure

- `mobile/` - Flutter Android and iOS application.
- `backend/` - FastAPI backend.
- `docs/` - Project feature documentation.
- `docker-compose.yml` - Local backend and PostgreSQL setup.

## Backend Setup

1. Install Docker.
2. Copy `backend/.env.example` to `backend/.env`.
3. Change the SECRET_KEY and admin credentials.
4. Run:

```bash
docker compose up --build
