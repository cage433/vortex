from unittest import TestCase

from sheets.sheet_range import CellCoordinates
from testing_utils import RandomisedTest


class CellCoordinatesTest(TestCase):
    def test_known_cases(self):
        self.assertEqual(CellCoordinates(i_row=0, i_col=0).text, "A1")
        self.assertEqual(CellCoordinates(i_row=10, i_col=0).text, "A11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=25).text, "Z11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26).text, "AA11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 + 25).text, "AZ11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 2).text, "BA11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 2 + 25).text, "BZ11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 3).text, "CA11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 26).text, "ZA11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 26 + 25).text, "ZZ11")
        self.assertEqual(CellCoordinates(i_row=10, i_col=26 * 27).text, "AAA11")

    @RandomisedTest(number_of_runs=100)
    def test_round_trip(self, rng):
        i_row = rng.randint(1, 100)
        i_col = rng.randint(1, 100)
        coords = CellCoordinates(i_row=i_row, i_col=i_col)
        coords2 = CellCoordinates(text=coords.text)
        self.assertEqual(coords2, coords)
        coords3 = CellCoordinates(i_row=coords.i_row, i_col=coords.i_col)
        self.assertEqual(coords3, coords)
