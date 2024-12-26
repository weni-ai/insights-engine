from random import randint
from django.test import TestCase
from django.utils.crypto import get_random_string

from insights.sources.flowruns.usecases.query_execute import transform_results_data


class TestFlowRunDataTransformation(TestCase):
    def setUp(self):
        counts = [randint(1, 10) for i in range(2)]

        self.total = sum(counts)
        self.terms_agg_buckets = []

        for count in counts:
            self.terms_agg_buckets.append(
                {"key": get_random_string(10), "doc_count": count}
            )

    def test_flowrun_data_transformation(self):
        results = transform_results_data(self.total, 0, self.terms_agg_buckets)

        for result in results:
            self.assertEqual(
                result["value"],
                round(((result["full_value"] / self.total) * 100), 2),
            )
