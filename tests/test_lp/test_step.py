"""Tests for LpStep, CreateVar, CreateConstr, and Publish."""

import pytest
from abc import ABC
from register import Register, RegisterKey, NumKey, Dimension
from or_algo.lp.symbol import VarKey, ConstrKey
from or_algo.lp.step import LpStep, CreateVar, CreateConstr, Publish
from ortools.linear_solver import pywraplp


class TestLpStep:
    def test_is_abstract(self):
        assert issubclass(LpStep, ABC)

    def test_cannot_instantiate_directly(self):
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            LpStep(symbol=vk)

    def test_requires_run_method(self):
        class InvalidStep(LpStep):
            pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            InvalidStep(symbol=vk)

    def test_concrete_subclass(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteStep(symbol=vk)
        assert step._symbol is vk

    def test_accepts_varkey(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteStep(symbol=vk)
        assert isinstance(step._symbol, VarKey)

    def test_accepts_constrkey(self):
        class ConcreteStep(LpStep):
            def run(self, data, model, var):
                pass
        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        step = ConcreteStep(symbol=ck)
        assert isinstance(step._symbol, ConstrKey)


class TestCreateVar:
    def test_is_lp_step(self):
        assert issubclass(CreateVar, LpStep)
        assert issubclass(CreateVar, ABC)

    def test_cannot_instantiate_directly(self):
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        with pytest.raises(TypeError):
            CreateVar(symbol=vk)

    def test_concrete_subclass(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert step._symbol is vk

    def test_init_only_takes_symbol(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert not hasattr(step, '_weight')
        assert not hasattr(step, '_lb')
        assert not hasattr(step, '_ub')

    def test_vtype_continuous(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=float)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'CONTINUOUS'

    def test_vtype_integer(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=int)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'INTEGER'

    def test_vtype_binary(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x', vtype=bool)
        step = ConcreteCreateVar(symbol=vk)
        assert step.vtype == 'BINARY'

    def test_no_create_method(self):
        class ConcreteCreateVar(CreateVar):
            def run(self, data, model, var):
                pass
        vk = VarKey(id=1, name='X', name_cn='x', sign='x')
        step = ConcreteCreateVar(symbol=vk)
        assert not hasattr(step, '_create')


class TestCreateConstr:
    def test_is_lp_step(self):
        assert issubclass(CreateConstr, LpStep)
        assert issubclass(CreateConstr, ABC)

    def test_cannot_instantiate_directly(self):
        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        with pytest.raises(TypeError):
            CreateConstr(symbol=ck)

    def test_concrete_subclass(self):
        class ConcreteCreateConstr(CreateConstr):
            def run(self, data, model, var):
                pass
        ck = ConstrKey(id=1, name='C', name_cn='c', sign='c')
        step = ConcreteCreateConstr(symbol=ck)
        assert step._symbol is ck


class TestPublish:
    @pytest.fixture
    def setup(self):
        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=float)

        var_reg = Register()
        v0 = model.NumVar(0, 10, 'v0')
        v1 = model.NumVar(0, 10, 'v1')
        var_reg[vk][(d,)][(0,)] = v0
        var_reg[vk][(d,)][(1,)] = v1

        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetCoefficient(v1, 1)
        model.Objective().SetMaximization()
        model.Add(v0 <= 3.7)
        model.Add(v1 <= 5.2)
        model.Solve()

        return model, d, vk, var_reg

    def test_publish_writes_solution_to_data(self, setup):
        model, d, vk, var_reg = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)
        result = data[vk][d,]
        assert (0,) in result
        assert (1,) in result

    def test_publish_threshold_filters_small_values(self, setup):
        model, d, vk, var_reg = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), threshold=100.0)
        pub.run(data, model, var_reg)
        result = data[vk][d,]
        assert len(result) == 0

    def test_publish_zeros_includes_zero_values(self, setup):
        model, d, vk, var_reg = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), zeros=True)
        pub.run(data, model, var_reg)
        result = data[vk][d,]
        assert (0,) in result
        assert (1,) in result

    def test_publish_int_vtype_rounds(self):
        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=int)

        var_reg = Register()
        v0 = model.IntVar(0, 10, 'v0')
        var_reg[vk][(d,)][(0,)] = v0

        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetMaximization()
        model.Add(v0 <= 7)
        model.Solve()

        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)
        val = data[vk][(d,)][(0,)]
        assert isinstance(val, int)
        assert val == 7

    def test_publish_bool_vtype(self):
        model = pywraplp.Solver.CreateSolver('SCIP')
        d = Dimension('Item', '物料', 'I')
        vk = VarKey(id=1, name='X', name_cn='x', sign='X', vtype=bool)

        var_reg = Register()
        v0 = model.IntVar(0, 1, 'v0')
        var_reg[vk][(d,)][(0,)] = v0

        model.Objective().SetCoefficient(v0, 1)
        model.Objective().SetMaximization()
        model.Solve()

        data = Register()
        pub = Publish(symbol=vk, dimension=(d,))
        pub.run(data, model, var_reg)
        val = data[vk][(d,)][(0,)]
        assert isinstance(val, bool)
        assert val is True

    def test_publish_target_none_selects_all(self, setup):
        model, d, vk, var_reg = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), target=None)
        pub.run(data, model, var_reg)
        result = data[vk][d,]
        assert (0,) in result
        assert (1,) in result

    def test_publish_target_with_slice(self, setup):
        model, d, vk, var_reg = setup
        data = Register()
        pub = Publish(symbol=vk, dimension=(d,), target=(slice(0, 1),))
        pub.run(data, model, var_reg)
        result = data[vk][d,]
        assert (0,) in result
        assert len(result) == 1
