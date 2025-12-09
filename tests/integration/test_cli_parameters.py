"""Integration tests for CLI parameter conversion patterns.

Tests validate that typing_graph correctly extracts metadata needed for
CLI argument configuration, based on patterns from the
cli_parameter_conversion.py example.
"""

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Annotated
from typing_extensions import Doc

from annotated_types import Gt, Lt, MinLen

from typing_graph import (
    inspect_dataclass,
    inspect_enum,
)
from typing_graph._node import (
    is_concrete_node,
    is_dataclass_node,
    is_enum_node,
    is_subscripted_generic_node,
    is_union_type_node,
)

from .conftest import (
    LogLevel,
    Priority,
    find_metadata_of_type,
    has_metadata_of_type,
)

if TYPE_CHECKING:
    from collections.abc import Callable


@dataclass(frozen=True, slots=True)
class CLIArg:
    """CLI argument configuration."""

    short: str | None = None
    long: str | None = None
    help: str | None = None


@dataclass(frozen=True, slots=True)
class EnvVar:
    """Environment variable fallback for configuration."""

    name: str


@dataclass(frozen=True, slots=True)
class Converter:
    """Custom converter function for parsing."""

    func: "Callable[[str], object]"


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    """Database configuration with CLI and env var metadata."""

    host: Annotated[str, CLIArg(long="--db-host"), Doc("Database hostname")]
    port: Annotated[
        int, Gt(0), Lt(65536), CLIArg(short="-P", long="--db-port"), EnvVar("DB_PORT")
    ]
    username: str
    password: Annotated[str, EnvVar("DB_PASSWORD")]


@dataclass(frozen=True, slots=True)
class ServerConfig:
    """Server configuration with nested database config."""

    name: Annotated[str, CLIArg(long="--name"), MinLen(1)]
    port: Annotated[int, Gt(0), Lt(65536), CLIArg(short="-p", long="--port")]
    log_level: LogLevel = LogLevel.INFO
    db: DatabaseConfig | None = None


class TestCLIArgMetadataExtraction:
    def test_cliarg_short_extracted(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        cliarg = find_metadata_of_type(port_field.metadata, CLIArg)
        assert cliarg is not None
        assert cliarg.short == "-P"

    def test_cliarg_long_extracted(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        cliarg = find_metadata_of_type(port_field.metadata, CLIArg)
        assert cliarg is not None
        assert cliarg.long == "--db-port"

    def test_cliarg_with_only_long(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        host_field = next(f for f in result.fields if f.name == "host")

        cliarg = find_metadata_of_type(host_field.metadata, CLIArg)
        assert cliarg is not None
        assert cliarg.short is None
        assert cliarg.long == "--db-host"

    def test_cliarg_with_short_and_long(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        cliarg = find_metadata_of_type(port_field.metadata, CLIArg)
        assert cliarg is not None
        assert cliarg.short == "-p"
        assert cliarg.long == "--port"


class TestEnvVarMetadataExtraction:
    def test_envvar_name_extracted(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        envvar = find_metadata_of_type(port_field.metadata, EnvVar)
        assert envvar is not None
        assert envvar.name == "DB_PORT"

    def test_envvar_on_password_field(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        password_field = next(f for f in result.fields if f.name == "password")

        envvar = find_metadata_of_type(password_field.metadata, EnvVar)
        assert envvar is not None
        assert envvar.name == "DB_PASSWORD"

    def test_cliarg_and_envvar_combined(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        # Should have both
        assert has_metadata_of_type(port_field.metadata, CLIArg)
        assert has_metadata_of_type(port_field.metadata, EnvVar)


class TestConverterMetadataExtraction:
    def test_converter_extracted(self) -> None:
        @dataclass
        class ConfigWithConverter:
            start_date: Annotated[date, Converter(date.fromisoformat)]

        result = inspect_dataclass(ConfigWithConverter)

        assert is_dataclass_node(result)
        date_field = next(f for f in result.fields if f.name == "start_date")

        converter = find_metadata_of_type(date_field.metadata, Converter)
        assert converter is not None
        assert converter.func == date.fromisoformat

    def test_converter_with_constraints(self) -> None:
        @dataclass
        class ConfigWithConverterAndConstraints:
            value: Annotated[int, Converter(int), Gt(0), Lt(100)]

        result = inspect_dataclass(ConfigWithConverterAndConstraints)

        assert is_dataclass_node(result)
        value_field = next(f for f in result.fields if f.name == "value")

        # Should have all three
        assert has_metadata_of_type(value_field.metadata, Converter)
        assert has_metadata_of_type(value_field.metadata, Gt)
        assert has_metadata_of_type(value_field.metadata, Lt)


class TestNestedConfigInspection:
    def test_server_config_has_db_field(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        db_field = next(f for f in result.fields if f.name == "db")

        # db is DatabaseConfig | None
        assert is_union_type_node(db_field.type)

    def test_nested_config_type_accessible(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        db_field = next(f for f in result.fields if f.name == "db")

        assert is_union_type_node(db_field.type)

        # Find DatabaseConfig member
        db_type = None
        for member in db_field.type.members:
            if is_concrete_node(member) and member.cls is DatabaseConfig:
                db_type = member
                break

        assert db_type is not None

    def test_nested_config_can_be_inspected(self) -> None:
        # Inspect DatabaseConfig from ServerConfig.db
        db_result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(db_result)
        field_names = {f.name for f in db_result.fields}
        assert field_names == {"host", "port", "username", "password"}

    def test_nested_config_field_metadata(self) -> None:
        # DatabaseConfig.port has CLIArg and EnvVar
        db_result = inspect_dataclass(DatabaseConfig)

        port_field = next(f for f in db_result.fields if f.name == "port")
        assert has_metadata_of_type(port_field.metadata, CLIArg)
        assert has_metadata_of_type(port_field.metadata, EnvVar)

    def test_doc_metadata_on_nested_field(self) -> None:
        db_result = inspect_dataclass(DatabaseConfig)

        host_field = next(f for f in db_result.fields if f.name == "host")
        doc = find_metadata_of_type(host_field.metadata, Doc)
        assert doc is not None
        assert doc.documentation == "Database hostname"


class TestEnumFieldForChoices:
    def test_enum_field_detected(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        log_level_field = next(f for f in result.fields if f.name == "log_level")

        # Type should be LogLevel (concrete type)
        assert is_concrete_node(log_level_field.type)
        assert log_level_field.type.cls is LogLevel

    def test_enum_members_for_choices(self) -> None:
        # Inspect enum to get choices for CLI argument
        result = inspect_enum(LogLevel)

        assert is_enum_node(result)
        member_names = [name for name, _ in result.members]
        assert member_names == ["DEBUG", "INFO", "WARNING", "ERROR"]

    def test_enum_values_for_validation(self) -> None:
        result = inspect_enum(LogLevel)

        assert is_enum_node(result)
        member_values = [value for _, value in result.members]
        assert member_values == ["debug", "info", "warning", "error"]

    def test_int_enum_for_numeric_choices(self) -> None:
        result = inspect_enum(Priority)

        assert is_enum_node(result)
        member_dict = dict(result.members)
        assert member_dict["LOW"] == 1
        assert member_dict["MEDIUM"] == 2
        assert member_dict["HIGH"] == 3


class TestDefaultValueExtraction:
    def test_field_with_default_not_required(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        log_level_field = next(f for f in result.fields if f.name == "log_level")

        assert log_level_field.required is False

    def test_field_without_default_is_required(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        name_field = next(f for f in result.fields if f.name == "name")

        assert name_field.required is True

    def test_optional_field_not_required(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        db_field = next(f for f in result.fields if f.name == "db")

        assert db_field.required is False


class TestConstraintExtraction:
    def test_port_range_constraints(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        gt = find_metadata_of_type(port_field.metadata, Gt)
        lt = find_metadata_of_type(port_field.metadata, Lt)

        assert gt is not None
        assert gt.gt == 0

        assert lt is not None
        assert lt.lt == 65536

    def test_string_length_constraint(self) -> None:
        result = inspect_dataclass(ServerConfig)

        assert is_dataclass_node(result)
        name_field = next(f for f in result.fields if f.name == "name")

        minlen = find_metadata_of_type(name_field.metadata, MinLen)
        assert minlen is not None
        assert minlen.min_length == 1


class TestListFieldForMultipleValues:
    def test_list_field_detected(self) -> None:
        @dataclass
        class ConfigWithList:
            allowed_hosts: Annotated[list[str], MinLen(1)]

        result = inspect_dataclass(ConfigWithList)

        assert is_dataclass_node(result)
        hosts_field = next(f for f in result.fields if f.name == "allowed_hosts")

        assert is_subscripted_generic_node(hosts_field.type)

    def test_list_element_type(self) -> None:
        @dataclass
        class ConfigWithList:
            ports: list[int]

        result = inspect_dataclass(ConfigWithList)

        assert is_dataclass_node(result)
        ports_field = next(f for f in result.fields if f.name == "ports")

        assert is_subscripted_generic_node(ports_field.type)
        element = ports_field.type.args[0]

        assert is_concrete_node(element)
        assert element.cls is int


class TestCombinedMetadataDiscovery:
    def test_all_metadata_types_on_field(self) -> None:
        @dataclass
        class FullyAnnotatedConfig:
            port: Annotated[
                int,
                CLIArg(short="-p", long="--port"),
                EnvVar("PORT"),
                Gt(0),
                Lt(65536),
                Doc("Server port number"),
            ]

        result = inspect_dataclass(FullyAnnotatedConfig)

        assert is_dataclass_node(result)
        port_field = next(f for f in result.fields if f.name == "port")

        # All metadata should be present
        assert has_metadata_of_type(port_field.metadata, CLIArg)
        assert has_metadata_of_type(port_field.metadata, EnvVar)
        assert has_metadata_of_type(port_field.metadata, Gt)
        assert has_metadata_of_type(port_field.metadata, Lt)
        assert has_metadata_of_type(port_field.metadata, Doc)

    def test_metadata_values_correct(self) -> None:
        @dataclass
        class FullyAnnotatedConfig:
            port: Annotated[
                int,
                CLIArg(short="-p", long="--port"),
                EnvVar("PORT"),
                Gt(0),
                Lt(65536),
                Doc("Server port number"),
            ]

        result = inspect_dataclass(FullyAnnotatedConfig)
        port_field = next(f for f in result.fields if f.name == "port")

        cliarg = find_metadata_of_type(port_field.metadata, CLIArg)
        assert cliarg is not None
        assert cliarg.short == "-p"
        assert cliarg.long == "--port"

        envvar = find_metadata_of_type(port_field.metadata, EnvVar)
        assert envvar is not None
        assert envvar.name == "PORT"

        gt = find_metadata_of_type(port_field.metadata, Gt)
        assert gt is not None
        assert gt.gt == 0

        lt = find_metadata_of_type(port_field.metadata, Lt)
        assert lt is not None
        assert lt.lt == 65536

        doc_info = find_metadata_of_type(port_field.metadata, Doc)
        assert doc_info is not None
        assert doc_info.documentation == "Server port number"


class TestConfigTraversalForArgumentGeneration:
    def test_collect_all_cliargs(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)

        cliargs: list[tuple[str, CLIArg]] = []
        for field_def in result.fields:
            cliarg = find_metadata_of_type(field_def.metadata, CLIArg)
            if cliarg:
                cliargs.append((field_def.name, cliarg))

        # host and port have CLIArg
        assert len(cliargs) == 2
        names = {name for name, _ in cliargs}
        assert names == {"host", "port"}

    def test_collect_all_envvars(self) -> None:
        result = inspect_dataclass(DatabaseConfig)

        assert is_dataclass_node(result)

        envvars: list[tuple[str, EnvVar]] = []
        for field_def in result.fields:
            envvar = find_metadata_of_type(field_def.metadata, EnvVar)
            if envvar:
                envvars.append((field_def.name, envvar))

        # port and password have EnvVar
        assert len(envvars) == 2
        names = {name for name, _ in envvars}
        assert names == {"port", "password"}

    def test_nested_config_argument_collection(self) -> None:
        # Collect all CLIArgs from both ServerConfig and nested DatabaseConfig
        server_result = inspect_dataclass(ServerConfig)
        db_result = inspect_dataclass(DatabaseConfig)

        all_cliargs: list[tuple[str, CLIArg]] = []

        for dataclass_result in [server_result, db_result]:
            assert is_dataclass_node(dataclass_result)
            for field_def in dataclass_result.fields:
                cliarg = find_metadata_of_type(field_def.metadata, CLIArg)
                if cliarg:
                    all_cliargs.append((field_def.name, cliarg))

        # ServerConfig: name, port (2)
        # DatabaseConfig: host, port (2)
        assert len(all_cliargs) == 4
