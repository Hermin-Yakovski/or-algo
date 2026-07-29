"""Symbol hierarchy for LP model elements."""

from __future__ import annotations

import itertools
from typing import TYPE_CHECKING, Any

from ortools.linear_solver import pywraplp
from register import NumKey, RegisterKey, Selected, delegable

if TYPE_CHECKING:
    from register import Register


class VarKey(NumKey):
    """Decision variable key that wraps a NumKey and adds LP-specific delegable methods."""

    _sign: str

    def __init__(self, id: int, name: str, name_cn: str, sign: str, vtype: type = float):
        super().__init__(id, name, name_cn, vtype)
        self._sign = sign

    @property
    def sign(self) -> str:
        return self._sign

    def validate(self, selected: Selected, **kwargs: Any) -> dict[tuple[int, ...], bool]:
        return {k: isinstance(v, pywraplp.Variable) for k, v in selected.items()}

    @delegable
    def sum(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:  # type: ignore[override]
        dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
        idx_str = ",".join(str(i) for i in next(iter(selected)))
        name = f"{self.sign}({dim_signs},MTC,)({idx_str},1,)"
        sum_var = model.NumVar(-model.infinity(), model.infinity(), name)
        model.Add(sum_var == sum(selected.values()), name=f"{name}_constr")
        return sum_var

    @delegable
    def max(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:  # type: ignore[override]
        dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
        idx_str = ",".join(str(i) for i in next(iter(selected)))
        name = f"{self.sign}({dim_signs},MTC,)({idx_str},2,)"
        max_var = model.NumVar(-model.infinity(), model.infinity(), name)
        for idx, var in selected.items():
            i_str = ",".join(str(i) for i in idx)
            model.Add(max_var >= var, name=f"{self.sign}({dim_signs},MTC,)({i_str},2,)")
        return max_var

    @delegable
    def min(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:  # type: ignore[override]
        dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
        idx_str = ",".join(str(i) for i in next(iter(selected)))
        name = f"{self.sign}({dim_signs},MTC,)({idx_str},3,)"
        min_var = model.NumVar(-model.infinity(), model.infinity(), name)
        for idx, var in selected.items():
            i_str = ",".join(str(i) for i in idx)
            model.Add(min_var <= var, name=f"{self.sign}({dim_signs},MTC,)({i_str},3,)")
        return min_var

    @delegable
    def range(self, selected: Selected, *, model: pywraplp.Solver) -> pywraplp.Variable:  # type: ignore[override]
        dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
        idx_str = ",".join(str(i) for i in next(iter(selected)))
        name = f"{self.sign}({dim_signs},MTC,)({idx_str},4,)"
        range_var = model.NumVar(0, model.infinity(), name)
        for (idx1, v1), (idx2, v2) in itertools.permutations(selected.items(), 2):
            i_str = ",".join(str(i) for i in idx1 + idx2)
            model.Add(range_var >= v1 - v2, name=f"{self.sign}({dim_signs},MTC,)({i_str},4,)")
        return range_var

    @delegable
    def set_weight(
        self, selected: Selected, *, model: pywraplp.Solver, weight: Register[NumKey]
    ) -> None:
        w_space = weight[self][selected._dims,]  # type: ignore[attr-defined]
        for index, var in selected.items():
            w = w_space[index,] if index in w_space else 0
            model.Objective().SetCoefficient(var, w)

    @delegable
    def set_lb(self, selected: Selected, *, model: pywraplp.Solver, lb: Register[NumKey]) -> None:
        lb_space = lb[self][selected._dims,]  # type: ignore[attr-defined]
        for index, var in selected.items():
            if index in lb_space:
                dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
                idx_str = ",".join(str(i) for i in index)
                model.Add(var >= lb_space[index,], name=f"{self.sign}({dim_signs},)({idx_str},)_lb")

    @delegable
    def set_ub(self, selected: Selected, *, model: pywraplp.Solver, ub: Register[NumKey]) -> None:
        ub_space = ub[self][selected._dims,]  # type: ignore[attr-defined]
        for index, var in selected.items():
            if index in ub_space:
                dim_signs = ",".join(d.sign for d in selected._dims)  # type: ignore[attr-defined]
                idx_str = ",".join(str(i) for i in index)
                model.Add(var <= ub_space[index,], name=f"{self.sign}({dim_signs},)({idx_str},)_ub")


class ConstrKey(RegisterKey):
    """Constraint key for LP model constraints."""

    _id: int
    _name: str
    _name_cn: str
    _sign: str

    def __init__(self, id: int, name: str, name_cn: str, sign: str):
        self._id = id
        self._name = name
        self._name_cn = name_cn
        self._sign = sign

    @property
    def id(self) -> int:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def name_cn(self) -> str:
        return self._name_cn

    @property
    def sign(self) -> str:
        return self._sign

    def validate(self, selected: Selected, **kwargs: Any) -> dict[tuple[int, ...], bool]:
        return {k: isinstance(v, pywraplp.Constraint) for k, v in selected.items()}

    def __str__(self) -> str:
        return self._name
