import copy
import sys
import unittest
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from northwind_lakehouse import validate, decimal


class SourceValidationTests(unittest.TestCase):
    def setUp(self):
        self.data = dict(customers=[dict(customer_id='C1')],
                         products=[dict(product_id=1)], shippers=[dict(shipper_id=1)],
                         orders=[dict(order_id=1, customer_id='C1', shipper_id=1, freight=Decimal('100'))],
                         order_details=[dict(line_id=1, order_id=1, product_id=1,
                                             quantity=2, unit_price=Decimal('10'), discount=Decimal('.1'))])

    def test_valid_source_and_exact_dimension_duplicate(self):
        self.data['customers'].append(dict(customer_id='C1'))
        validate(self.data)
        self.assertEqual(len(self.data['customers']), 1)

    def test_conflicting_dimension_rejected(self):
        self.data['customers'].append(dict(customer_id='C1', city='different'))
        with self.assertRaisesRegex(ValueError, 'Conflicting duplicate'):
            validate(self.data)

    def test_orphan_rejected_instead_of_silently_losing_sales(self):
        self.data['order_details'][0]['product_id'] = 99
        with self.assertRaisesRegex(ValueError, 'Orphan'):
            validate(self.data)

    def test_invalid_discount_and_quantity(self):
        for key, value in [('discount', Decimal('10')), ('quantity', 0)]:
            data = copy.deepcopy(self.data)
            data['order_details'][0][key] = value
            with self.assertRaisesRegex(ValueError, 'Invalid sales measure'):
                validate(data)

    def test_nonfinite_rejected(self):
        for value in ['NaN', 'Infinity']:
            with self.assertRaises(ValueError):
                decimal(value)


if __name__ == '__main__':
    unittest.main()
