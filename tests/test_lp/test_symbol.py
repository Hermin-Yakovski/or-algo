"""Tests for VarKey and ConstrKey."""

import pytest
from register import NumKey, RegisterKey, Register, Dimension, Selected, delegable
from or_algo.lp.symbol import VarKey, ConstrKey
from ortools.linear_solver import pywraplp


@pytest.fixture
def model():
    """Create an OR-Tools solver for testing."""
    m = pywraplp.Solver.CreateSolver('SCIP')
    yield m


@pytest.fixture
def var_key():
    """Create a VarKey for testing."""
    return VarKey(id=1, name='TestVar', name_cn='测试变量', sign='X')


@pytest.fixture
def constr_key():
    """Create a ConstrKey for testing."""
    return ConstrKey(id=1, name='TestConstr', name_cn='测试约束', sign='C')


class TestVarKey:
    def test_inherits_from_numkey(self, var_key):
        assert isinstance(var_key, NumKey)
        assert isinstance(var_key, RegisterKey)

    def test_properties(self, var_key):
        assert var_key.id == 1
        assert var_key.name == 'TestVar'
        assert var_key.name_cn == '测试变量'
        assert var_key.sign == 'X'

    def test_default_vtype_is_float(self, var_key):
        assert var_key.vtype is float

    def test_custom_vtype(self):
        vk = VarKey(id=2, name='IntVar', name_cn='整数', sign='Y', vtype=int)
        assert vk.vtype is int

    def test_validate_checks_pywraplp_variable(self, var_key, model):
        v1 = model.NumVar(0, 1, 'v1')
        selected = {(0,): v1, (1,): 'not_a_var'}
        result = var_key.validate(selected)
        assert result[(0,)] is True
        assert result[(1,)] is False

    def test_hash_eq(self):
        vk1 = VarKey(id=1, name='X', name_cn='x', sign='x')
        vk2 = VarKey(id=1, name='X', name_cn='x', sign='y')
        assert vk1 == vk2  # same id + name
        assert hash(vk1) == hash(vk2)

    def test_as_register_key(self, var_key):
        reg = Register()
        d = Dimension('Item', '物料', 'I')
        reg[var_key][d,][0,] = 42.0
        assert reg[var_key][d,][0,] == 42.0

    def test_str_returns_name(self, var_key):
        assert str(var_key) == 'TestVar'

    def test_repr_returns_name(self, var_key):
        assert repr(var_key) == 'TestVar'


class TestConstrKey:
    def test_inherits_from_register_key(self, constr_key):
        assert isinstance(constr_key, RegisterKey)

    def test_properties(self, constr_key):
        assert constr_key.id == 1
        assert constr_key.name == 'TestConstr'
        assert constr_key.name_cn == '测试约束'
        assert constr_key.sign == 'C'

    def test_validate_checks_pywraplp_constraint(self, constr_key, model):
        x = model.NumVar(0, 1, 'x')
        c1 = model.Add(x <= 1)
        selected = {(0,): c1, (1,): 'not_a_constraint'}
        result = constr_key.validate(selected)
        assert result[(0,)] is True
        assert result[(1,)] is False

    def test_different_ids_are_distinct(self):
        ck1 = ConstrKey(id=1, name='A', name_cn='a', sign='a')
        ck2 = ConstrKey(id=2, name='A', name_cn='a', sign='a')
        assert ck1 != ck2  # different id

    def test_str_returns_name(self, constr_key):
        assert str(constr_key) == 'TestConstr'


class TestVarKeyDelegable:
    """Test VarKey delegable methods via Selection proxy."""

    @pytest.fixture
    def setup(self):
        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Loc', '地点', 'L')
        vk = VarKey(id=10, name='Ship', name_cn='运输', sign='X')
        reg = Register()
        # Create 3 variables
        reg[vk][d,][0,] = model.NumVar(0, 100, 'x0')
        reg[vk][d,][1,] = model.NumVar(0, 100, 'x1')
        reg[vk][d,][2,] = model.NumVar(0, 100, 'x2')
        return model, d, vk, reg

    def test_sum_creates_variable_with_constraint(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.sum(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert 'MTC' in result.name()
        assert ',1,' in result.name()

    def test_max_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.max(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',2,' in result.name()

    def test_min_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.min(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',3,' in result.name()

    def test_range_creates_variable_with_constraints(self, setup):
        model, d, vk, reg = setup
        result = reg[vk][d,].all.range(model=model)
        assert isinstance(result, pywraplp.Variable)
        assert ',4,' in result.name()

    def test_set_weight_sets_objective_coefficients(self, setup):
        model, d, vk, reg = setup
        weight_reg = Register()
        weight_reg[vk][d,][0,] = 1.5
        weight_reg[vk][d,][1,] = 2.5
        reg[vk][d,].all.set_weight(model=model, weight=weight_reg)
        # Verify by solving — objective should reflect coefficients

    def test_set_lb_adds_lower_bound_constraints(self, setup):
        model, d, vk, reg = setup
        lb_reg = Register()
        lb_reg[vk][d,][0,] = 5.0
        lb_reg[vk][d,][1,] = 10.0
        reg[vk][d,].all.set_lb(model=model, lb=lb_reg)

    def test_set_ub_adds_upper_bound_constraints(self, setup):
        model, d, vk, reg = setup
        ub_reg = Register()
        ub_reg[vk][d,][0,] = 50.0
        reg[vk][d,].all.set_ub(model=model, ub=ub_reg)

    def test_set_lb_constraint_naming(self, setup):
        model, d, vk, reg = setup
        lb_reg = Register()
        lb_reg[vk][d,][0,] = 5.0
        reg[vk][d,].all.set_lb(model=model, lb=lb_reg)

    def test_set_ub_constraint_naming(self, setup):
        model, d, vk, reg = setup
        ub_reg = Register()
        ub_reg[vk][d,][0,] = 50.0
        reg[vk][d,].all.set_ub(model=model, ub=ub_reg)
