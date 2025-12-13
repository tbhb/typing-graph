# pyright: reportAny=false, reportExplicitAny=false
# pyright: reportPrivateUsage=false
from typing import Any

from hypothesis import given, settings, strategies as st

from typing_graph._namespace import extract_class_namespace, merge_namespaces

namespace_dict = st.dictionaries(
    st.text(min_size=1, max_size=10, alphabet="abcdefghijklmnopqrstuvwxyz"),
    st.one_of(st.integers(), st.text(max_size=20), st.booleans()),
    max_size=10,
)


class TestMergeNamespacesProperties:
    @given(
        auto_global=namespace_dict,
        auto_local=namespace_dict,
    )
    @settings(deadline=None)
    def test_merge_with_none_user_returns_auto_copy(
        self,
        auto_global: dict[str, Any],
        auto_local: dict[str, Any],
    ) -> None:
        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, None, None
        )
        assert merged_global == auto_global
        assert merged_local == auto_local
        assert merged_global is not auto_global
        assert merged_local is not auto_local

    @given(
        auto_global=namespace_dict,
        auto_local=namespace_dict,
        user_global=namespace_dict,
        user_local=namespace_dict,
    )
    @settings(deadline=None)
    def test_user_keys_always_present_in_merged(
        self,
        auto_global: dict[str, Any],
        auto_local: dict[str, Any],
        user_global: dict[str, Any],
        user_local: dict[str, Any],
    ) -> None:
        merged_global, merged_local = merge_namespaces(
            auto_global, auto_local, user_global, user_local
        )
        for key, value in user_global.items():
            assert key in merged_global
            assert merged_global[key] == value
        for key, value in user_local.items():
            assert key in merged_local
            assert merged_local[key] == value

    @given(
        auto_global=namespace_dict,
        auto_local=namespace_dict,
        user_global=namespace_dict,
        user_local=namespace_dict,
    )
    @settings(deadline=None)
    def test_merge_does_not_modify_inputs(
        self,
        auto_global: dict[str, Any],
        auto_local: dict[str, Any],
        user_global: dict[str, Any],
        user_local: dict[str, Any],
    ) -> None:
        auto_global_copy = dict(auto_global)
        auto_local_copy = dict(auto_local)
        user_global_copy = dict(user_global)
        user_local_copy = dict(user_local)

        _ = merge_namespaces(auto_global, auto_local, user_global, user_local)

        assert auto_global == auto_global_copy
        assert auto_local == auto_local_copy
        assert user_global == user_global_copy
        assert user_local == user_local_copy


class TestExtractNamespaceInvariants:
    @given(st.sampled_from([int, str, float, bool, list, dict, set, tuple]))
    @settings(deadline=None)
    def test_extract_class_namespace_always_returns_tuple(self, cls: type) -> None:
        result = extract_class_namespace(cls)
        assert isinstance(result, tuple)
        assert len(result) == 2
        globalns, localns = result
        assert isinstance(globalns, dict)
        assert isinstance(localns, dict)

    @given(st.sampled_from([int, str, float, bool, list, dict, set, tuple]))
    @settings(deadline=None)
    def test_class_in_own_local_namespace(self, cls: type) -> None:
        _globalns, localns = extract_class_namespace(cls)
        class_name = cls.__name__
        assert class_name in localns
        assert localns[class_name] is cls
