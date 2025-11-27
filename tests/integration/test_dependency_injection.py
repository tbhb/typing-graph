"""Integration tests for dependency injection patterns.

Tests validate that typing_graph correctly extracts metadata and type
information needed for DI container implementations, based on patterns
from the dependency_injection.py example.
"""

from dataclasses import dataclass
from typing import (
    TYPE_CHECKING,
    Annotated,
    Generic,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from typing_graph import (
    inspect_class,
    inspect_dataclass,
    inspect_function,
)
from typing_graph._node import (
    is_concrete_type,
    is_dataclass_type_node,
    is_function_node,
    is_protocol_type_node,
    is_signature_node,
    is_union_type_node,
)

from .conftest import (
    find_metadata_of_type,
    has_metadata_of_type,
)

if TYPE_CHECKING:
    from collections.abc import Callable


# ============================================================================
# Metadata markers - DI patterns (from dependency_injection.py example)
# ============================================================================


@dataclass(frozen=True, slots=True)
class Inject:
    """Mark a parameter for dependency injection."""


@dataclass(frozen=True, slots=True)
class Singleton:
    """Configure singleton scope for a dependency."""


@dataclass(frozen=True, slots=True)
class Transient:
    """Configure transient scope (new instance per request)."""


@dataclass(frozen=True, slots=True)
class Scoped:
    """Configure scoped lifetime (per-request in web apps)."""


@dataclass(frozen=True, slots=True)
class Qualifier:
    """Disambiguate between multiple implementations of the same interface."""

    name: str


@dataclass(frozen=True, slots=True)
class Factory:
    """Provide a factory function for lazy instantiation."""

    func: "Callable[[], object]"


@dataclass(frozen=True, slots=True)
class OptionalDep:
    """Mark dependency as optional (inject None if unavailable)."""


@dataclass(frozen=True, slots=True)
class Lazy:
    """Defer instantiation until first access."""


# ============================================================================
# Protocol interfaces (from dependency_injection.py)
# ============================================================================


class Logger(Protocol):
    """Logging service interface."""

    def log(self, message: str, *, level: str = "INFO") -> None: ...
    def error(self, message: str, *, exc: BaseException | None = None) -> None: ...


class Database(Protocol):
    """Database service interface."""

    def query(self, sql: str) -> list[dict[str, object]]: ...
    def execute(self, sql: str) -> int: ...


@runtime_checkable
class Cache(Protocol):
    """Cache service interface (runtime checkable)."""

    def get(self, key: str) -> object | None: ...
    def set(self, key: str, value: object, ttl: int | None = None) -> None: ...


# ============================================================================
# DI service classes (from dependency_injection.py)
# ============================================================================


@dataclass
class PostgresDatabase:
    """Database implementation with injected dependencies."""

    connection_string: Annotated[str, Inject(), Qualifier("db_connection_string")]
    logger: Annotated[Logger, Inject(), Singleton()]


@dataclass
class UserRepository:
    """Repository with required and optional dependencies."""

    db: Annotated[Database, Inject()]
    logger: Annotated[Logger, Inject()]
    cache: Annotated[Cache | None, Inject(), OptionalDep()]


@dataclass
class UserService:
    """Service with nested repository dependency."""

    repo: Annotated[UserRepository, Inject()]
    logger: Annotated[Logger, Inject()]


# ============================================================================
# Generic types (from dependency_injection.py)
# ============================================================================

T = TypeVar("T")


@dataclass(slots=True)
class LazyInstance(Generic[T]):
    """Lazy wrapper for deferred dependency resolution."""

    _factory: "Callable[[], T]"
    _instance: T | None = None

    def get(self) -> T:
        if self._instance is None:
            self._instance = self._factory()
        return self._instance


class TestConstructorParameterInspection:
    def test_dataclass_init_returns_function_node(self) -> None:
        result = inspect_function(UserService.__init__)

        assert is_function_node(result)
        assert result.name == "__init__"

    def test_dataclass_init_has_signature_node(self) -> None:
        result = inspect_function(UserService.__init__)

        assert is_function_node(result)
        assert is_signature_node(result.signature)

    def test_dataclass_init_extracts_all_parameters(self) -> None:
        result = inspect_function(UserService.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        # Should have self, repo, and logger
        assert "self" in params
        assert "repo" in params
        assert "logger" in params

    def test_parameter_type_is_inspected(self) -> None:
        result = inspect_function(UserService.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        repo_param = params["repo"]
        # The type should reference UserRepository
        assert is_concrete_type(repo_param.type)
        assert repo_param.type.cls is UserRepository

    def test_parameter_metadata_is_extracted(self) -> None:
        result = inspect_function(UserService.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        repo_param = params["repo"]
        # Metadata should be extracted from Annotated
        assert has_metadata_of_type(repo_param.metadata, Inject)


class TestAnnotatedParameterMetadata:
    def test_single_inject_marker_extracted(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        db_param = params["db"]
        inject = find_metadata_of_type(db_param.metadata, Inject)
        assert inject is not None

    def test_singleton_scope_marker_extracted(self) -> None:
        result = inspect_function(PostgresDatabase.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        logger_param = params["logger"]
        singleton = find_metadata_of_type(logger_param.metadata, Singleton)
        assert singleton is not None

    def test_qualifier_with_name_extracted(self) -> None:
        result = inspect_function(PostgresDatabase.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        conn_param = params["connection_string"]
        qualifier = find_metadata_of_type(conn_param.metadata, Qualifier)
        assert qualifier is not None
        assert qualifier.name == "db_connection_string"

    def test_multiple_metadata_markers_preserved(self) -> None:
        result = inspect_function(PostgresDatabase.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        conn_param = params["connection_string"]
        # Should have both Inject and Qualifier
        assert has_metadata_of_type(conn_param.metadata, Inject)
        assert has_metadata_of_type(conn_param.metadata, Qualifier)

    def test_optional_marker_extracted(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        cache_param = params["cache"]
        optional = find_metadata_of_type(cache_param.metadata, OptionalDep)
        assert optional is not None


class TestOptionalDependencyDetection:
    def test_union_with_none_detected(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        cache_param = params["cache"]
        # cache is Annotated[Cache | None, ...] so type should be union
        assert is_union_type_node(cache_param.type)

    def test_union_members_include_none(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        cache_param = params["cache"]
        assert is_union_type_node(cache_param.type)

        member_types: set[type[object]] = set()
        for member in cache_param.type.members:
            if is_concrete_type(member):
                member_types.add(member.cls)

        assert type(None) in member_types

    def test_union_members_include_protocol_type(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        cache_param = params["cache"]
        assert is_union_type_node(cache_param.type)

        has_cache = False
        for member in cache_param.type.members:
            if is_concrete_type(member) and member.cls is Cache:
                has_cache = True
                break

        assert has_cache

    def test_non_optional_dependency_is_not_union(self) -> None:
        result = inspect_function(UserRepository.__init__)

        assert is_function_node(result)
        params = {p.name: p for p in result.signature.parameters}

        db_param = params["db"]
        # db is Annotated[Database, Inject()] - not optional
        assert not is_union_type_node(db_param.type)


class TestProtocolTypeInspection:
    def test_protocol_detected_by_inspect_class(self) -> None:
        result = inspect_class(Logger)

        assert is_protocol_type_node(result)
        assert result.name == "Logger"

    def test_protocol_has_methods(self) -> None:
        result = inspect_class(Logger)

        assert is_protocol_type_node(result)
        method_names = {m.name for m in result.methods}
        assert "log" in method_names
        assert "error" in method_names

    def test_protocol_method_signature_inspected(self) -> None:
        result = inspect_class(Logger)

        assert is_protocol_type_node(result)
        log_method = next(m for m in result.methods if m.name == "log")
        assert is_signature_node(log_method.signature)

        param_names = {p.name for p in log_method.signature.parameters}
        assert "self" in param_names
        assert "message" in param_names
        assert "level" in param_names

    def test_runtime_checkable_protocol_detected(self) -> None:
        result = inspect_class(Cache)

        assert is_protocol_type_node(result)
        assert result.is_runtime_checkable is True

    def test_non_runtime_checkable_protocol_detected(self) -> None:
        result = inspect_class(Logger)

        assert is_protocol_type_node(result)
        assert result.is_runtime_checkable is False


class TestNestedServiceDependencies:
    def test_dataclass_fields_inspected(self) -> None:
        result = inspect_dataclass(UserService)

        assert is_dataclass_type_node(result)
        assert len(result.fields) == 2

    def test_field_names_match_dataclass_fields(self) -> None:
        result = inspect_dataclass(UserService)

        assert is_dataclass_type_node(result)
        field_names = {f.name for f in result.fields}
        assert field_names == {"repo", "logger"}

    def test_nested_dependency_type_is_dataclass(self) -> None:
        result = inspect_dataclass(UserService)

        assert is_dataclass_type_node(result)
        repo_field = next(f for f in result.fields if f.name == "repo")

        assert is_concrete_type(repo_field.type)
        assert repo_field.type.cls is UserRepository

    def test_field_metadata_extracted(self) -> None:
        result = inspect_dataclass(UserService)

        assert is_dataclass_type_node(result)
        repo_field = next(f for f in result.fields if f.name == "repo")

        assert has_metadata_of_type(repo_field.metadata, Inject)


class TestDependencyGraphTraversal:
    def test_two_level_dependency_chain(self) -> None:
        # UserService -> UserRepository -> Database
        service_result = inspect_dataclass(UserService)
        assert is_dataclass_type_node(service_result)

        repo_field = next(f for f in service_result.fields if f.name == "repo")
        assert is_concrete_type(repo_field.type)
        assert repo_field.type.cls is UserRepository

        # Now inspect the nested dependency
        repo_result = inspect_dataclass(UserRepository)
        assert is_dataclass_type_node(repo_result)

        db_field = next(f for f in repo_result.fields if f.name == "db")
        assert has_metadata_of_type(db_field.metadata, Inject)

    def test_all_inject_markers_in_chain(self) -> None:
        # Verify Inject markers propagate through the chain
        service_result = inspect_dataclass(UserService)
        repo_result = inspect_dataclass(UserRepository)
        db_result = inspect_dataclass(PostgresDatabase)

        # All should have Inject on their dependencies
        for result in [service_result, repo_result, db_result]:
            assert is_dataclass_type_node(result)
            for field_def in result.fields:
                assert has_metadata_of_type(field_def.metadata, Inject)


class TestDynamicServiceDefinition:
    def test_dynamically_defined_service_inspected(self) -> None:
        @dataclass
        class DynamicService:
            dep: Annotated[str, Inject(), Qualifier("config")]

        result = inspect_function(DynamicService.__init__)
        assert is_function_node(result)

        params = {p.name: p for p in result.signature.parameters}
        dep_param = params["dep"]

        assert has_metadata_of_type(dep_param.metadata, Inject)
        qualifier = find_metadata_of_type(dep_param.metadata, Qualifier)
        assert qualifier is not None
        assert qualifier.name == "config"

    def test_service_with_protocol_dependency(self) -> None:
        @dataclass
        class ServiceWithProtocol:
            logger: Annotated[Logger, Inject()]
            db: Annotated[Database, Inject(), Singleton()]

        result = inspect_dataclass(ServiceWithProtocol)
        assert is_dataclass_type_node(result)

        fields = {f.name: f for f in result.fields}

        logger_field = fields["logger"]
        assert is_concrete_type(logger_field.type)
        assert logger_field.type.cls is Logger

        db_field = fields["db"]
        assert has_metadata_of_type(db_field.metadata, Singleton)
