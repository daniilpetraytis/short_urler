# URL Shortener Service with FastAPI

## Quick Start

0. For very quick start:
    The service is running on a remote server at the address **158.160.137.113**. You can check its availability using the following commands:

    ```bash
    curl http://158.160.137.113:8000
    curl http://158.160.137.113:8000/docs
    ```

1. Configure environment variables:
   ```bash
   cp src/.env.sample src/.env
   ```

2. Launch the service:
   ```bash
   docker-compose up --build
   ```

## Technical Stack

- **Backend**: FastAPI framework
- **Database**: PostgreSQL (with Alembic migrations)
- **Caching**: Redis
- **Deployment**: Docker & Docker Compose

## Architecture

The service stores URL mappings in PostgreSQL and implements Redis caching for improved performance. Database schema definitions can be found in the `migrations` directory.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/links/shorten` | POST | Create a shortened URL. Parameters:<br>- `url`: Original URL (required)<br>- `alias`: Custom short code (optional)<br>- `expires_at`: Expiration date (optional) |
| `/links/{short_code}` | GET | Redirect to the original URL |
| `/links/{short_code}` | DELETE | Remove a URL mapping |
| `/links/{short_code}` | PUT | Update the URL mapping |
| `/links/{short_code}/stats` | GET | View usage statistics for the URL |

## Features

- Custom aliases for shortened URLs
- URL expiration settings
- Usage statistics tracking
- High-performance caching

## Testing

The project includes comprehensive tests to ensure functionality and reliability:

- **Functional Tests**: Located in the `test_api.py` file, these tests verify the complete functionality of the API endpoints.
- **Unit Tests**: Found in the `test_unit.py` file, these tests focus on individual components and units of the application to ensure they work as expected.

These tests provide confidence in the operation and quality of the code.
