# Gold & Silver Jewellery Management — Full-stack source package

This package contains:
- `mobile/`: Flutter Android/iOS client source
- `backend/`: FastAPI REST backend with JWT authentication, shop memberships, role checks, PostgreSQL persistence, audit events and JSON backup export
- `docker-compose.yml`: local PostgreSQL + API deployment
- `docs/FEATURE_MATRIX.md`: included features and remaining production work

## Start backend
1. Install Docker Desktop or Docker Engine.
2. Copy `backend/.env.example` to `backend/.env`.
3. Change `SECRET_KEY`, `BOOTSTRAP_ADMIN_EMAIL`, `BOOTSTRAP_ADMIN_PASSWORD`, and database password.
4. Run `docker compose up --build`.
5. Open `http://localhost:8000/docs` for API documentation.
6. Health check: `http://localhost:8000/health`.

The first configured bootstrap account is the Super Admin. Keep credentials private and change the example values before running.

## Start mobile app
1. Install Flutter stable and Android Studio; use Xcode on macOS for iOS.
2. In `mobile/`, run `flutter pub get`.
3. Run `flutter analyze`, then `flutter test` (add device tests before release).
4. For Android emulator, API base URL defaults to `http://10.0.2.2:8000`.
5. For a physical phone, enter the computer/server LAN IP and port 8000 in the API URL field. For production, use an HTTPS domain.
6. Run `flutter run`; release APK: `flutter build apk --release`.

## Offline behaviour
The mobile app caches records in SQLite. New records created while the API is unreachable are queued locally and can be pushed with the Sync button when online. This is an initial offline queue, not a complete conflict-resolution engine. Use the backend version field and review conflicts; do not assume every offline edit can be merged automatically.

## Important production note
This is an implementation source package and backend starter, not a signed app-store release or a production-hosted SaaS. It has not been compiled, deployed, penetration-tested or tested on physical Android/iOS devices in this environment. See `docs/FEATURE_MATRIX.md` for exact coverage and remaining tasks. A production service still requires deployment, HTTPS, secret rotation, migrations, backup/restore drills and acceptance testing.
