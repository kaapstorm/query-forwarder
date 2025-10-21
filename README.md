query-forwarder
===============

Forwards a SQL query response to a web API.


Environment Variables
---------------------

The following environment variables can be configured:

* **`DATABASE_URL`** (required): PostgreSQL connection string for the
  query-forwarder database

  + Format: `postgresql+asyncpg://user:password@host:port/database`
  + Used by: Web app, CLI tool, Alembic migrations

* **`ENCRYPTION_KEY`** (required for production): 32-byte encryption key
  for AES-256-GCM encryption of API passwords

  + Format: Hex-encoded string (64 characters)
  + Generate with:
    ```shell
    $ python3 -c "from query_forwarder.crypto import EncryptionService; print(EncryptionService.generate_key().hex())"
    ```
  + If not set, the application will not be able to encrypt/decrypt API
    passwords.

Example `.env` file:

```shell
DATABASE_URL=postgresql+asyncpg://user:password@localhost/query_forwarder
ENCRYPTION_KEY=0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef
```


Command Line Tool
-----------------

Usage:

```shell
$ cd query_forwarder
$ ./forward.py <domain_name>
```


Running The Web App
-------------------

```shell
$ cd query_forwarder
$ uv run quart --app query_forwarder.app run
```

The app will be available at http://localhost:5000
