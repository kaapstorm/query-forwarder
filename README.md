query-forwarder
===============

Forwards a SQL query response to a web API.

Command Line Tool
-----------------

Usage:

```shell
$ cd query_forwarder
$ ./forward <domain_name>
```

Running The Web App
-------------------

```shell
$ cd query_forwarder
$ uv run quart --app query_forwarder.app run
```

The app will be available at http://localhost:5000
