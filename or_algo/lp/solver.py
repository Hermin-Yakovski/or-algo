"""LpSolver: Linear Programming solver using OR-Tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from ortools.linear_solver import pywraplp

from ..solver import Solver
from . import exception

if TYPE_CHECKING:
    from typing import Any

    from or_register import Register, RegisterKey

    from or_algo.lp.step import LpStep
    from or_algo.lp.symbol import VarKey


class LpSolver(Solver):
    """Linear Programming solver using OR-Tools.

    Inherits from or-algo's Solver base class and integrates
    with Register[RegisterKey] for data flow.
    """

    _name: str
    _var: Register[VarKey]
    _build_steps: list[tuple[type[LpStep], tuple[Any, ...], dict[str, Any]]]
    _publish_steps: list[tuple[tuple[Any, ...], dict[str, Any]]]
    _model: pywraplp.Solver
    _solver_type: str

    def __init__(self, name: str, solver_type: str = "SCIP"):
        from or_register import Register

        super().__init__(name)
        self._name = name
        self._var = Register()
        self._build_steps = []
        self._publish_steps = []
        self._solver_type = solver_type

        self._model = pywraplp.Solver.CreateSolver(solver_type)
        if not self._model:
            raise exception.LpSolverException(
                f"Failed to create OR-Tools solver with type '{solver_type}'"
            )
        self._model.Objective().SetMaximization()

    @property
    def solver_type(self) -> str:
        return self._solver_type

    def publish(self, *args: Any, **kwargs: Any) -> None:
        self._publish_steps.append((args, kwargs))

    def append(self, step: type[LpStep], *args: Any, **kwargs: Any) -> None:
        """Add a build step to the execution sequence.

        Args:
            step: LpStep subclass (CreateVar or CreateConstr)
            *args: Arguments to pass to step.__init__()
            **kwargs: Keyword arguments to pass to step.__init__()

        Raises:
            LpSolverException: If step type is unsupported
        """
        from or_algo.lp.step import CreateConstr, CreateVar

        if issubclass(step, (CreateVar, CreateConstr)):
            self._build_steps.append((step, args, kwargs))
        else:
            raise exception.LpSolverException(
                f"Unsupported step type {step} in {type(self).__name__}.append()"
            )

    def solve(self, data: Register[RegisterKey]) -> Register[RegisterKey]:
        """Build and solve the LP model.

        Args:
            data: Register containing input parameters

        Returns:
            The same Register (users can extract solutions via their own mechanisms)

        Raises:
            BuildLpStepException: If a build step fails
            LpModelOptimizeException: If optimization fails or no solution is found
        """
        from or_algo.lp import Publish

        # Execute build steps
        for step_type, args, kwargs in self._build_steps:
            try:
                step_type(*args, **kwargs).run(data, self._model, self._var)
            except Exception as e:
                raise exception.BuildLpStepException(
                    f"Failed {step_type.__name__}.run()! args={args}, kwargs={kwargs}"
                ) from e

        self._model.EnableOutput()

        # write model to .lp file
        with open(f"{self._name}.lp", "w") as f:
            f.write(self._model.ExportModelAsLpFormat(False))

        # Solve the model
        status = self._model.Solve()

        # Handle OR-Tools status codes
        if status == pywraplp.Solver.OPTIMAL:
            for args, kwargs in self._publish_steps:
                Publish(*args, **kwargs).run(data, self._model, self._var)
            return data
        elif status == pywraplp.Solver.INFEASIBLE:
            raise exception.LpModelOptimizeException("Model is infeasible")
        elif status == pywraplp.Solver.UNBOUNDED:
            raise exception.LpModelOptimizeException("Model is unbounded")
        elif status == pywraplp.Solver.NOT_SOLVED:
            raise exception.LpModelOptimizeException("Model was not solved")
        elif status == pywraplp.Solver.ABNORMAL:
            raise exception.LpModelOptimizeException("Solver encountered an error")
        else:
            raise exception.LpModelOptimizeException(f"No solution found! status={status}")
