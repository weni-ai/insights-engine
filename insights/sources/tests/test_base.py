from django.test import TestCase

from insights.sources.base import BaseQueryExecutor


class ConcreteQueryExecutor(BaseQueryExecutor):
    @classmethod
    def execute(cls, *args, **kwargs):
        return {"executed": True}


class TestBaseQueryExecutor(TestCase):
    def test_cannot_instantiate_abstract_class(self):
        with self.assertRaises(TypeError):
            BaseQueryExecutor()

    def test_concrete_subclass_can_be_instantiated(self):
        executor = ConcreteQueryExecutor()
        self.assertIsInstance(executor, BaseQueryExecutor)

    def test_concrete_subclass_execute_returns_expected(self):
        result = ConcreteQueryExecutor.execute()
        self.assertEqual(result, {"executed": True})

    def test_incomplete_subclass_raises_type_error(self):
        with self.assertRaises(TypeError):

            class IncompleteExecutor(BaseQueryExecutor):
                pass

            IncompleteExecutor()
