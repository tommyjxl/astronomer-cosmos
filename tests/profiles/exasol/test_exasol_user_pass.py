"Tests for the Exasol profile."

from unittest.mock import patch

import pytest
from airflow.models.connection import Connection

from cosmos.profiles.exasol.user_pass import (
    ExasolUserPasswordProfileMapping,
)


@pytest.fixture()
def mock_exasol_connection():  # type: ignore
    """
    Sets the connection as an environment variable.
    """
    conn = Connection(
        conn_id="my_exasol_connection",
        conn_type="exasol",
        host="my_host",
        login="my_user",
        password="my_password",
        port=8563,
        schema="my_database",
        extra='{"protocol_version": "1"}',
    )

    with patch("airflow.hooks.base.BaseHook.get_connection", return_value=conn):
        yield conn


def test_profile_args(
    mock_exasol_connection: Connection,
) -> None:
    """
    Tests that the profile values get set correctly.
    """
    profile_mapping = ExasolUserPasswordProfileMapping(
        mock_exasol_connection.conn_id,
        profile_args={"schema": "my_schema", "threads": 1},
    )

    assert profile_mapping.profile == {
        "type": mock_exasol_connection.conn_type,
        "dsn": f"{mock_exasol_connection.host}:{mock_exasol_connection.port}",
        "user": mock_exasol_connection.login,
        "password": "{{ env_var('COSMOS_CONN_EXASOL_PASSWORD') }}",
        "dbname": mock_exasol_connection.schema,
        "schema": "my_schema",
        "threads": 1,
        "protocol_version": "1",
    }


def test_profile_args_overrides(
    mock_exasol_connection: Connection,
) -> None:
    """
    Tests that you can override the profile values.
    """
    profile_mapping = ExasolUserPasswordProfileMapping(
        mock_exasol_connection.conn_id,
        profile_args={
            "dsn": "my_dsn_override",
            "user": "my_user_override",
            "password": "my_password_override",
            "schema": "my_schema",
            "dbname": "my_db_override",
            "threads": 1,
            "protocol_version": "2",
        },
    )

    assert profile_mapping.profile == {
        "type": mock_exasol_connection.conn_type,
        "dsn": "my_dsn_override",
        "user": "my_user_override",
        "password": "{{ env_var('COSMOS_CONN_EXASOL_PASSWORD') }}",
        "dbname": "my_db_override",
        "schema": "my_schema",
        "threads": 1,
        "protocol_version": "2",
    }


def test_profile_env_vars(
    mock_exasol_connection: Connection,
) -> None:
    """
    Tests that the environment variables get set correctly.
    """
    profile_mapping = ExasolUserPasswordProfileMapping(
        mock_exasol_connection.conn_id,
        profile_args={"schema": "my_schema", "threads": 1},
    )
    assert profile_mapping.env_vars == {
        "COSMOS_CONN_EXASOL_PASSWORD": mock_exasol_connection.password,
    }


def test_dsn_formatting() -> None:
    """
    Tests that the DSN gets set correctly when a user specifies a port.
    """
    # first, test with a host that includes a port
    conn = Connection(
        conn_id="my_exasol_connection",
        conn_type="exasol",
        host="my_host:1000",
        login="my_user",
        password="my_password",
        schema="my_database",
    )

    with patch("airflow.hooks.base.BaseHook.get_connection", return_value=conn):
        profile_mapping = ExasolUserPasswordProfileMapping(conn, {"schema": "my_schema", "threads": 1})
        assert profile_mapping.dsn == "my_host:1000"

    # next, test with a host that doesn't include a port
    conn = Connection(
        conn_id="my_exasol_connection",
        conn_type="exasol",
        host="my_host",
        login="my_user",
        password="my_password",
        schema="my_database",
    )

    with patch("airflow.hooks.base.BaseHook.get_connection", return_value=conn):
        profile_mapping = ExasolUserPasswordProfileMapping(conn, {"schema": "my_schema", "threads": 1})
        assert profile_mapping.dsn == "my_host:8563"  # should default to 8563

    # lastly, test with a port override
    conn = Connection(
        conn_id="my_exasol_connection",
        conn_type="exasol",
        host="my_host",
        login="my_user",
        password="my_password",
        port=1000,  # different than the default
        schema="my_database",
    )

    with patch("airflow.hooks.base.BaseHook.get_connection", return_value=conn):
        profile_mapping = ExasolUserPasswordProfileMapping(conn, {"schema": "my_schema", "threads": 1})
        assert profile_mapping.dsn == "my_host:1000"
