from __future__ import annotations


class StoutPlusEntityMixin:
    _stout_suggested_object_id: str

    @property
    def suggested_object_id(self) -> str | None:
        return self._stout_suggested_object_id
