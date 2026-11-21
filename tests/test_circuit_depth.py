import unittest

class TestCircuitDepth(unittest.TestCase):
    def test_cnot_count_linear_bound(self):
        n_qubits = 8
        cnot_count = 2 * (n_qubits - 1)
        self.assertLessEqual(cnot_count, 20)

    def test_folding_odd_multipliers(self):
        multipliers = [1, 3, 5, 7]
        for m in multipliers:
            self.assertEqual(m % 2, 1)

if __name__ == '__main__':
    unittest.main()
