"""LpSolver: Linear Programming solver using OR-Tools."""

from typing import TYPE_CHECKING, Any, Type

if TYPE_CHECKING:
    from register import Register, Parameter
    from or_algo.lp.symbol import Symbol
    from or_algo.lp.step import LpStep
    from ortools.linear_solver import pywraplp

from ortools.linear_solver import pywraplp

from ..solver import Solver
from . import exception
from .step import CreateConstrCalculateMetric


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

    def append(self, step: Type["LpStep"], *args: Any, **kwargs: Any) -> None:
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

    def solve(self, data: "Register[Parameter]") -> "Register[Parameter]":
        """Build and solve the LP model.

        Args:
            data: Register containing input parameters

        Returns:
            The same Register (users can extract solutions via their own mechanisms)

        Raises:
            BuildLpStepException: If a build step fails
            LpModelOptimizeException: If optimization fails or no solution is found
        """
        self.append(CreateConstrCalculateMetric,)

        # Execute build steps
        for step_type, args, kwargs in self._build_steps:
            try:
                step_type(*args, **kwargs).run(data, self._model, self._var)
            except Exception as e:
                raise exception.BuildLpStepException(
                    f"Failed {step_type.__name__}.run()! args={args}, kwargs={kwargs}"
                ) from e

        # Solve the model
        status = self._model.Solve()

        # Handle OR-Tools status codes
        if status == pywraplp.Solver.OPTIMAL:
            pass  # Users handle solution extraction
        elif status == pywraplp.Solver.INFEASIBLE:
            raise exception.LpModelOptimizeException("Model is infeasible")
        elif status == pywraplp.Solver.UNBOUNDED:
            raise exception.LpModelOptimizeException("Model is unbounded")
        elif status == pywraplp.Solver.NOT_SOLVED:
            raise exception.LpModelOptimizeException("Model was not solved")
        elif status == pywraplp.Solver.ABNORMAL:
            raise exception.LpModelOptimizeException("Solver encountered an error")
        else:
            raise exception.LpModelOptimizeException(
                f"No solution found! status={status}"
            )

        return data
