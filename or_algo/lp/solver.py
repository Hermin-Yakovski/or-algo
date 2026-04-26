"""LpSolver: Linear Programming solver using OR-Tools."""

from typing import TYPE_CHECKING, Any, Type

if TYPE_CHECKING:
    from register import Register
    from or_algo.lp.symbol import Symbol
    from or_algo.lp.step import LpStep
    from ortools.linear_solver import pywraplp

from ortools.linear_solver import pywraplp
from or_algo.solver import Solver
from . import exception


class LpSolver(Solver):
    """Linear Programming solver using OR-Tools.

    Inherits from or-algo's Solver base class and integrates
    with Register[Parameter] for data flow.
    """

    _name: str
    _weight: "Register[Symbol]"
    _lb: "Register[Symbol]"
    _ub: "Register[Symbol]"
    _var: "Register[Symbol]"
    _build_steps: list[tuple[Type["LpStep"], tuple[Any, ...], dict[str, Any]]]
    _model: pywraplp.Solver
    _solver_type: str

    def __init__(
        self,
        name: str,
        weight: "Register[Symbol]" = None,
        lb: "Register[Symbol]" = None,
        ub: "Register[Symbol]" = None,
        solver_type: str = 'CBC'
    ):
        from register import Register

        super().__init__(name)
        self._name = name
        self._weight = Register() if weight is None else weight
        self._lb = Register() if lb is None else lb
        self._ub = Register() if ub is None else ub
        self._var = Register()
        self._build_steps = list()
        self._solver_type = solver_type

        self._model = pywraplp.Solver.CreateSolver(solver_type)
        if not self._model:
            raise exception.LpSolverException(
                f"Failed to create OR-Tools solver with type '{solver_type}'"
            )

    @property
    def solver_type(self) -> str:
        return self._solver_type
