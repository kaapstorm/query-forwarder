query-forwarder
===============

The purpose of **query-forwarder** is to call a given SQL query and
to send the response in the body of a POST or PUT request to a web API
endpoint. The query response, the web API request, and the web API
response are all logged.


Tech stack
----------

* Server-side language: Python 3.13
* Web framework: Quart
* ORM: SQLAlchemy 2.0 with asyncpg
* Front-end libraries:
  + HTMX
  + Alpine.js
  + Bootstrap 5
  + Websockets for live API logs


Database
--------

**query-forwarder** uses PostgreSQL for persistence. This includes the
logs for query responses, web API requests, and web API responses, and
the data structures detailed below.


Data Structures
---------------

**query-forwarder** is a multi-tenant web app.

Tenants are stored as Domain instances:

| Domain                                  |
|-----------------------------------------|
| id (auto-increment integer primary key) |
| name (unique index)                     |

A user belongs to one or more domains:

| User                  |
|-----------------------|
| id (UUID primary key) |
| email                 |
| first_name            |
| last_name             |

| DomainUser          |
|---------------------|
| domain_id (integer) |
| user_id (UUID)      |

Configuration is stored per domain:

| DomainConfig               |
|----------------------------|
| domain_id (integer unique) |
| db_uri (varchar 255)       |
| db_query (text)            |
| api_auth_type              |
| api_username (varchar 255) |
| api_password (varchar 255) |
| api_endpoint (varchar 255) |
| api_request_type           |

For initial implementation, `DomainConfig.api_auth_type` is limited to
'basic'.

Valid values for `DomainConfig.api_request_type` are 'post' and 'put'.

`DomainConfig.api_password` is stored encrypted using AES-256-GCM
(Advanced Encryption Standard with 256-bit keys in Galois/Counter Mode).
The password is encrypted using a secret key that is unique to the
instance of the **query-forwarder** web app.


Command Line Interface
----------------------

Forwarding a query result to an API endpoint can be done using the
`forward.py` command line tool. Usage:

```shell
$ cd query_forwarder
$ ./forward.py <domain_name>
```
