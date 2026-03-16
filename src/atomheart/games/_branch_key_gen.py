"""Small reusable branch-key generators for atomheart games."""

# pylint: disable=invalid-name

from __future__ import annotations

from typing import TYPE_CHECKING, TypeVar

import valanga

if TYPE_CHECKING:
    from collections.abc import Iterator, Sequence

TBranchKey_co = TypeVar("TBranchKey_co", covariant=True)


class TupleBranchKeyGen[TBranchKey_co](
    valanga.BranchKeyGeneratorP[TBranchKey_co],
):
    """Small resettable in-memory branch-key generator."""

    sort_branch_keys: bool = False

    def __init__(self, keys: Sequence[TBranchKey_co]) -> None:
        """Store branch keys for deterministic iteration."""
        self._keys = tuple(keys)
        self._index = 0

    @property
    def all_generated_keys(self) -> Sequence[TBranchKey_co] | None:
        """Return all branch keys known to this generator."""
        return self._keys

    def __iter__(self) -> Iterator[TBranchKey_co]:
        """Return the iterator protocol self."""
        return self

    def __next__(self) -> TBranchKey_co:
        """Return the next branch key or raise ``StopIteration``."""
        if self._index >= len(self._keys):
            raise StopIteration
        key = self._keys[self._index]
        self._index += 1
        return key

    def more_than_one(self) -> bool:
        """Return whether more than one branch key is available."""
        return len(self._keys) > 1

    def get_all(self) -> Sequence[TBranchKey_co]:
        """Return all branch keys as a new list."""
        return list(self._keys)

    def copy_with_reset(self) -> TupleBranchKeyGen[TBranchKey_co]:
        """Return a fresh generator reset to the first branch key."""
        return TupleBranchKeyGen(self._keys)
