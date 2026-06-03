"""LpStep hierarchy for LP model building."""
from abc import ABC, abstractmethod
import itertools
from typing import TYPE_CHECKING

from register import Register, Metric

from . import exception

if TYPE_CHECKING:
    from typing import Callable, Optional, Tuple

    from ortools.linear_solver import pywraplp
    from register import Dimension, Parameter

    from .symbol import Symbol, Var, Constr

class LpStep(ABC):
    """Abstract base class for LP model building steps."""

    def __init__(self, symbol: "Symbol"):
        super().__init__()
        self._symbol = symbol

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Execute this step to build the LP model.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        pass


class CreateVar(LpStep, ABC):
    """Base class for variable creation steps."""

    _weight: "Register[Symbol]"
    _lb: "Register[Symbol]"
    _ub: "Register[Symbol]"

    def __init__(
        self,
        symbol: "Var",
        weight: "Register[Symbol]",
        lb: "Register[Symbol]",
        ub: "Register[Symbol]"
    ):
        super().__init__(symbol)
        self._weight = weight
        self._lb = lb
        self._ub = ub

    @property
    def vtype(self) -> str:
        """Map Parameter vtype to OR-Tools variable type."""
        vtype_mapping = {
            int: 'INTEGER',
            float: 'CONTINUOUS',
            bool: 'BINARY',  # OR-Tools uses [0,1] integer for binary
        }
        vtype = self._symbol.parameter.vtype
        if vtype not in vtype_mapping:
            raise ValueError(
                f"Unsupported Parameter vtype: {vtype}. "
                f"Supported types: {list(vtype_mapping.keys())}"
            )
        return vtype_mapping[vtype]

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Create variables in the model."""
        pass

    def _create(self, data: "Register[Parameter]", model: "pywraplp.Solver", var: "Register[Symbol]",
        primary_key: "Parameter",
        dimension: "Tuple[Dimension, ...]",
        weight: "Optional[float]" = None,
        lb: "Optional[float]" = None,
        ub: "Optional[float]" = None,
        *,
        min_weight: float = 1e-6,
        metric: "Optional[Method]" = None,
        which: "Optional[Tuple[bool, ...]]" = None,
        sense : str = 'minimize',
        clear: bool = False,
        skip: "Optional[Callable[[tuple[int, ...]], bool]]" = None,
        ) -> int:
        """
        Add variables in batch

        parameters
        ----------
        data : Register[Parameter]
            s.a. self.run()
        model : pywraplp.Solver
            OR-Tools solver instance
        var : Register[Symbol]
            s.a. self.run()
        primary_key : Parameter
            The parameter, usually Id, that specifies dimensions of the scenario. The implementation assumes that this
            parameter accepts only DimensionAsKey objects of which key is one-element tuple of Dimension.
        dimension : tuple[Dimension, ...]
            The dimension of the variables
        weight : float, default None
            If given, the weight of the variable, otherwise refer to self._weight: DimensionAsKey
        lb : float, default None
            If given, the lower bound of the variable, otherwise refer to self._lb: DimensionAsKey
        ub : float, default None
            If given, the upper bound of the variable, otherwise refer to self._ub: DimensionAsKey
            Note: None is treated as infinity for OR-Tools compatibility
        min_weight: float, default 1e-6
            Threshold by which the weight of variable would be regarded as 0, if its absolute value < min_weight. It's
            intended to enhance numerical stability and accelerate the solving session.
        metric : var.Int, default None
            If given, specifies the metric to be applied for the aggregation, otherwise aggregation won't be applied.
        which: tuple[bool, ...]
            Corresponds to argument 'dimension'. If given (prerequisite: metric is not None), specifies the dimension to
            be aggregated, otherwise aggregate all.
        sense : str, default 'minimize', choices=['minimize', 'maximize']
            Objective direction. Uses OR-Tools SetMinimization()/SetMaximization().
        clear : bool, default False
            Note: OR-Tools objectives accumulate coefficients differently than PySCIPOpt.
            This parameter is kept for backward compatibility but has limited effect.
        skip : Callable, default None
            Callable that accepts index: tuple[int, ...], and returns bool. Do not create variable of the index if True.

        return
        -------
        The number of variables added.

        notes
        -----
        OR-Tools API usage:
        - Variable creation: solver.BoolVar() for binary [0,1], solver.IntVar() for integer,
          solver.NumVar() for continuous
        - Objective: Uses solver.Objective().SetCoefficient() for accumulation and
          SetMinimization()/SetMaximization() for direction
        """
        if metric is None:
            which_ = tuple(False for _ in dimension)
        elif which is None:
            which_ = tuple(True for _ in dimension)
        elif len(which) != len(dimension):
            raise exception.BuildLpStepException(f"Invalid argument of CreateVars.create: length of which and dimension must be equal."
                f"Got dimension={dimension}, which={which} when creating variable {self._symbol}")
        else:
            which_ = tuple(which)

        # the dimension not to be aggregated
        dimension_: tuple[Dimension, ...] = dimension if metric is None else tuple(
            d for d, flag in zip(dimension, which_) if not flag)

        # the dimension of the variables
        dimension_final: tuple[Dimension, ...] = dimension
        if metric is not None:
            dimension_final += (Metric,)

        # delete to re-decide
        data[self._symbol.parameter].pop(dimension_final)

        count: int = 0
        for index_ in itertools.product(*[data.select(primary_key, (d,)) for d in dimension_]):
            it = iter(index_)
            index_final: tuple[int, ...] = tuple(Register.ALL if flag else next(it)[0] for flag in which_)
            if metric is not None:
                index_final += (metric,)
            if skip is not None and skip(index_final):
                continue

            name = '{0}({1},)({2},)'.format(
                self._symbol,
                ','.join(d.sign for d in dimension_final),
                ','.join(str(ix) for ix in index_final))
            vtype: str = self.vtype if metric is None else 'CONTINUOUS'
            lb_: float = self._lb[self._symbol][dimension_final].get(index_final, 0) if lb is None else lb
            ub_raw: Optional[float] = self._ub[self._symbol][dimension_final].get(index_final, None) if ub is None else ub
            ub_: float = ub_raw if ub_raw is not None else model.infinity()

            # Create variable using type-specific OR-Tools methods
            if vtype == 'INTEGER':
                variable = model.IntVar(lb_, ub_, name)
            elif vtype == 'BINARY':
                # in ortools, integral variables are recognized as binary when bounded within [0, 1]
                lb_ = 0 if lb_ < 0 else lb_
                ub_ = 1 if ub_ > 1 else ub_
                variable = model.IntVar(lb_, ub_, name)
            else:  # CONTINUOUS
                variable = model.NumVar(lb_, ub_, name)
            var[self._symbol][dimension_final][index_final] = variable
            count += 1

            if weight is None:
                if dimension_final in self._weight[self._symbol]:
                    weight_ = self._weight[self._symbol][dimension_final].get(index_final,
                        self._weight[self._symbol][dimension_final].get((Register.ALL,) * len(dimension_final), 0))
                else:
                    weight_ = 0
            else:
                weight_ = weight

            sign: int = -1 if sense == 'minimize' else 1

            if abs(weight_) > min_weight:
                # Use OR-Tools objective accumulation pattern
                model.Objective().SetCoefficient(variable, sign * weight_)

        return count


class CreateConstr(LpStep, ABC):
    """Base class for constraint creation steps."""

    def __init__(self, symbol: "Constr"):
        super().__init__(symbol)

    @abstractmethod
    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Create constraints in the model."""
        pass


class CreateConstrCalculateMetric(CreateConstr):
    """Create metric aggregation constraints for variables with Metric dimension.

    Supports SUM, MAX, MIN, and RANGE metrics from register.Register.
    Constraints are created but not stored.
    """

    def __init__(self):
        from or_algo.lp.symbol import Constr

        super().__init__(Constr('CalculateMetric', '', 'CalculateMetric'))

    def run(
        self,
        data: "Register[Parameter]",
        model: "pywraplp.Solver",
        var: "Register[Symbol]"
    ) -> None:
        """Create metric aggregation constraints for variables with Metric dimension.

        Args:
            data: Register containing input parameters
            model: OR-Tools solver instance
            var: Register for storing variables/constraints
        """
        from or_algo.lp.symbol import Var

        # Iterate through all Var instances in var
        for v in var:
            # Check each dimension for Metric
            for dimension in var[v]:
                # Skip if last dimension is not Metric
                if not dimension or dimension[-1] is not Metric:
                    continue

                # Extract base dimension (all except last)
                dimension_ = dimension[:-1]

                # Process each index in the metric dimension
                for index in var[v][dimension]:
                    metric = index[-1]

                    # Create constraint based on metric type
                    if metric is Register.SUM:
                        # metric_var == sum(base_vars)
                        metric_var = var[v][dimension][index]

                        # Get base indices by removing last element (metric type)
                        base_index_prefix = index[:-1]

                        # Sum all base variables that match the prefix
                        base_vars = [
                            var[v][dimension_][base_index]
                            for base_index in var.select(v, dimension_, base_index_prefix)
                        ]

                        # Create equality constraint
                        constraint = model.Add(
                            metric_var == sum(base_vars),
                            name=f'{self._symbol.name}-{v.sign}({",".join(d.sign for d in dimension)})({",".join(str(ix) for ix in index)})_'
                        )

                    elif metric is Register.MAX:
                        # metric_var >= each base_var (lower bound for maximum)
                        metric_var = var[v][dimension][index]
                        base_index_prefix = index[:-1]

                        for base_index in var.select(v, dimension_, base_index_prefix):
                            base_var = var[v][dimension_][base_index]
                            model.Add(
                                metric_var >= base_var,
                                name=f'{self._symbol.name}-{v.sign}({",".join(d.sign for d in dimension_)})({",".join(str(ix) for ix in base_index)})'
                            )

                    elif metric is Register.MIN:
                        # metric_var <= each base_var (upper bound for minimum)
                        metric_var = var[v][dimension][index]
                        base_index_prefix = index[:-1]

                        for base_index in var.select(v, dimension_, base_index_prefix):
                            base_var = var[v][dimension_][base_index]
                            model.Add(
                                metric_var <= base_var,
                                name=f'{self._symbol.name}-{v.sign}({",".join(d.sign for d in dimension_)})({",".join(str(ix) for ix in base_index)})'
                            )

                    elif metric is Register.RANGE:
                        # metric_var >= |base_var1 - base_var2| for all pairs
                        # Implemented as: metric_var >= base_var1 - base_var2 AND metric_var >= base_var2 - base_var1
                        # which is equivalent to: metric_var >= abs(base_var1 - base_var2)
                        metric_var = var[v][dimension][index]
                        base_index_prefix = index[:-1]
                        base_indices = list(var.select(v, dimension_, base_index_prefix))

                        # Create pairwise constraints for all permutations
                        for index1, index2 in itertools.permutations(base_indices, 2):
                            base_var1 = var[v][dimension_][index1]
                            base_var2 = var[v][dimension_][index2]
                            model.Add(
                                metric_var >= base_var1 - base_var2,
                                name=f'{self._symbol.name}-{v.sign}({",".join(d.sign for d in dimension_ * 2)})({",".join(str(ix) for ix in index1 + index2)})'
                            )

                    else:
                        raise exception.BuildLpStepException(
                            f"Unknown metric type: {metric}. Expected SUM, MAX, MIN, or RANGE."
                        )


class Publish(LpStep):
    _zeros: bool
    _dimension: "Tuple[Dimension, ...]"
    _threshold: float
    _target: "Tuple[int, ...]"

    def __init__(self, symbol: "Symbol", dimension: "Tuple[Dimension, ...]", target: "Tuple[int, ...]" = None, zeros: bool = False, threshold: float = 1e-6):
        super().__init__(symbol)
        self._dimension = dimension
        self._zeros = zeros
        self._threshold = threshold
        self._target = target

    def run(self, data: "Register[Parameter]", model: "pywraplp.Solver", register: "Register[Symbol]") -> None:
        for index in register.select(self._symbol, self._dimension, self._target):
            parameter = self._symbol.parameter
            quantity = register[self._symbol][self._dimension][index].solution_value()
            if parameter.vtype is int:
                quantity = int(round(quantity, 0))
            elif parameter.vtype is bool:
                quantity = bool(round(quantity, 0))
            elif parameter.vtype is float:
                pass
            else:
                raise AlgoServiceException(f"Unsupported vtype {parameter.vtype} while publishing variable {self._symbol.name}")

            if self._zeros or (quantity > self._threshold):
                key = self._symbol.parameter
                data[key][self._dimension][index] = quantity
                # logger.debug("[v] %s%s%s: %s" , key, self._dimension, index, quantity)
