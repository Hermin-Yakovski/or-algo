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

    def append(self, step: Type["LpStep"], *args, **kwargs) -> None:
        """Add a build step to the execution sequence.

        Args:
            step: LpStep subclass (CreateVar or CreateConstr)
            *args, **kwargs: Arguments to pass to step.__init__()

        Raises:
            LpSolverException: If step type is unsupported
        """
        from or_algo.lp.step import CreateVar, CreateConstr

        if issubclass(step, CreateVar):
            # Fill args with (weight, lb, ub) if not provided
            # CreateVar.__init__ expects: (symbol, weight, lb, ub)
            # If user provides only symbol, append weight, lb, ub
            # If user provides symbol + weight, append lb, ub
            # etc.
            default_args = (self._weight, self._lb, self._ub)
            # Calculate how many default args we need to append
            # args[0] is symbol, so we need up to 3 more args
            num_provided = len(args)
            num_needed = max(0, 4 - num_provided)  # 4 = symbol + weight + lb + ub
            full_args = args + default_args[:num_needed]
            self._build_steps.append((step, full_args, kwargs))
        elif issubclass(step, CreateConstr):
            self._build_steps.append((step, args, kwargs))
        else:
            raise exception.LpSolverException(
                f"Unsupported step type {step} in {type(self).__name__}.append()"
            )

    def solve(self, data):
        """Solve the LP model.

        Args:
            data: Register[Parameter] containing input parameters

        Returns:
            Solver status/result
        """
        # TODO: Implement in Task 11
        raise NotImplementedError("LpSolver.solve() will be implemented in Task 11")
