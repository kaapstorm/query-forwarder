#!/usr/bin/env python
"""Command line tool to forward query results to API endpoints."""
import asyncio
import base64
import json
import sys

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine

from query_forwarder.crypto import EncryptionService, get_encryption_service
from query_forwarder.database import get_session
from query_forwarder.models import APILog, Domain, DomainConfig


async def execute_query(db_uri: str, query: str) -> tuple[str | None, str | None]:
    """Execute a SQL query against the configured database.

    Args:
        db_uri: Database connection URI
        query: SQL query to execute

    Returns:
        Tuple of (result_json, error_message)
    """
    try:
        engine = create_async_engine(db_uri)
        async with engine.connect() as conn:
            result = await conn.execute(text(query))
            rows = result.fetchall()
            if rows:
                data = [dict(row._mapping) for row in rows]
            else:
                data = []
            await engine.dispose()
            return json.dumps(data, default=str), None
    except Exception as e:
        return None, str(e)


async def send_to_api(
    config: DomainConfig,
    data: str,
    encryption_service: EncryptionService,
) -> tuple[int | None, dict[str, str] | None, str | None, str | None]:
    """Send data to the configured API endpoint.

    Args:
        config: Domain configuration
        data: JSON data to send
        encryption_service: Service to decrypt password

    Returns:
        Tuple of (status_code, response_headers, response_body, error_message)
    """
    try:
        decrypted_password = encryption_service.decrypt(config.api_password)

        auth_header = base64.b64encode(
            f"{config.api_username}:{decrypted_password}".encode()
        ).decode()

        headers = {
            "Authorization": f"Basic {auth_header}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient() as client:
            if config.api_request_type.lower() == "post":
                response = await client.post(
                    config.api_endpoint, content=data, headers=headers
                )
            elif config.api_request_type.lower() == "put":
                response = await client.put(
                    config.api_endpoint, content=data, headers=headers
                )
            else:
                return None, None, None, f"Invalid request type: {config.api_request_type}"

            return (
                response.status_code,
                dict(response.headers),
                response.text,
                None,
            )
    except Exception as e:
        return None, None, None, str(e)


async def forward_query(domain_name: str) -> None:
    """Forward query results for a domain to its configured API endpoint.

    Args:
        domain_name: Name of the domain to process
    """
    async with get_session() as session:
        result = await session.execute(
            select(Domain).where(Domain.name == domain_name)
        )
        domain = result.scalar_one_or_none()

        if not domain:
            print(f"Error: Domain '{domain_name}' not found", file=sys.stderr)
            sys.exit(1)

        result = await session.execute(
            select(DomainConfig).where(DomainConfig.domain_id == domain.id)
        )
        config = result.scalar_one_or_none()

        if not config:
            print(
                f"Error: No configuration found for domain '{domain_name}'",
                file=sys.stderr,
            )
            sys.exit(1)

        try:
            encryption_service = get_encryption_service()
        except ValueError as err:
            print(f"Error: {err}", file=sys.stderr)
            sys.exit(1)

        print(f"Executing query for domain '{domain_name}'...")
        query_result, query_error = await execute_query(config.db_uri, config.db_query)

        if query_error:
            print(f"Query error: {query_error}", file=sys.stderr)
        else:
            print(f"Query executed successfully, got {len(query_result)} bytes of data")

        log_entry = APILog(
            domain_id=domain.id,
            query_result=query_result,
            query_error=query_error,
            request_method=config.api_request_type.upper(),
            request_url=config.api_endpoint,
        )

        if query_result:
            print(f"Sending data to {config.api_endpoint}...")
            (
                status_code,
                response_headers,
                response_body,
                response_error,
            ) = await send_to_api(config, query_result, encryption_service)

            log_entry.request_headers = json.dumps(
                {"Authorization": "Basic ***", "Content-Type": "application/json"}
            )
            log_entry.request_body = query_result
            log_entry.response_status_code = status_code
            log_entry.response_headers = (
                json.dumps(response_headers) if response_headers else None
            )
            log_entry.response_body = response_body
            log_entry.response_error = response_error

            if response_error:
                print(f"API request error: {response_error}", file=sys.stderr)
            else:
                print(f"API response: HTTP {status_code}")
                if response_body:
                    print(f"Response body: {response_body[:200]}...")

        session.add(log_entry)
        await session.commit()
        print(f"Logged to database with ID {log_entry.id}")


def main() -> None:
    """Main entry point for the forward.py CLI tool."""
    if len(sys.argv) != 2:
        print("Usage: forward.py <domain_name>", file=sys.stderr)
        sys.exit(1)

    domain_name = sys.argv[1]
    asyncio.run(forward_query(domain_name))


if __name__ == "__main__":
    main()
