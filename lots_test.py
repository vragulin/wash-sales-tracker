import copy
import datetime
import unittest
import io
import lots as lots_lib
import numpy as np
from functools import cmp_to_key

# Import global params from class namespaces for easier reference
GAINS_CODES = lots_lib.Lot.GAINS_CODES

# Useful function to compare a dict with gains with a list of tuple of gains
def test_dict_vs_vals(vals, d):
    """ pack values into a dict with keys = GAINS_CODES and compare vs.
        dictonary d.
        Assume that vals are arranged in the right ordes of GAINS_CODES
        
        Return: boolean - True if dictionary values are the same as 'values'
    """
    # Compare all dict values to the list, and treat np.nans as equal as well
    test = [((d[k] == v) or (np.isnan(d[k]) and np.isnan(v))) 
            for k,v in zip(GAINS_CODES, vals)]
    return(np.all(test))

#%% TestLots
class TestLots(unittest.TestCase):

    def assertSameLots(self, a, b):
        self.assertEqual(a, b, msg='Lots are not equal: \n{}\n{}'.format(a, b))

    def test_parse_valid_csv_file(self):
        csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,9/15/2014,9/14/2014,2000,2100,10/5/2014,1800,W,200,form1,'
            'lot1,lot3|lot4,true,true',
            '10,ABC,A,9/15/2014,,2000,,10/5/2014,1800,W,200,form2,lot2,,false,',
            '20,ABC,A,9/25/2014,,3000,,11/5/2014,1800,,,,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        expected_lots_rows = []
        expected_lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 14), 2000, 2100, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', ['lot3', 'lot4'], True, True))
        expected_lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 15), 2000, 2000, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form2', 'lot2', [], False, False))
        expected_lots_rows.append(lots_lib.Lot(20, 'ABC', 'A', datetime.date(
            2014, 9, 25), datetime.date(2014, 9, 25), 3000, 3000,
            datetime.date(2014, 11, 5), 1800, '', 0, '', '', [], False, False))
        expected_lots = lots_lib.Lots(expected_lots_rows)
        self.assertSameLots(lots, expected_lots)

    def test_parse_invalid_headers(self):
        csv_data = [
            'Num,Symbol,Description,Buy Date,Basis,Sell Date,'
            'Proceeds,Adjustment Code,Adjustment,Form Position,Buy Lot,'
            'Is Replacement',
            '10,ABC,A,9/15/2014,2000,10/5/2014,1800,,,lot1'
        ]
        with self.assertRaises(lots_lib.BadHeadersError):
            lots = lots_lib.Lots.create_from_csv_data(csv_data)

    def test_write_csv_data(self):
        lots_rows = []
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15), datetime.date(
                2014, 9, 14), 2000, 2100, datetime.date(2014, 10, 5), 1800,
            'W', 200, 'form1', 'lot1', ['lot3', 'lot4'], True, True))
        lots_rows.append(lots_lib.Lot(10, 'ABC', 'A', datetime.date(
            2014, 9, 15), datetime.date(2014, 9, 15), 2000, 2000,
            datetime.date(2014, 10, 5), 1800, 'W', 200, 'form2', 'lot2', [],
            False, False))
        lots_rows.append(lots_lib.Lot(20, 'ABC', 'A', datetime.date(
            2014, 9, 25), datetime.date(2014, 9, 25), 3000, 3000,
            datetime.date(2014, 11, 5), 1800, '', 0, '', '', [], False, False))
        lots = lots_lib.Lots(lots_rows)

        actual_output = io.StringIO()
        lots.write_csv_data(actual_output)

        expected_csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,09/15/2014,09/14/2014,2000,2100,10/05/2014,1800,W,200,'
            'form1,lot1,lot3|lot4,True,True',
            '10,ABC,A,09/15/2014,,2000,,10/05/2014,1800,W,200,form2,lot2,,,',
            '20,ABC,A,09/25/2014,,3000,,11/05/2014,1800,,,,_1,,,'
        ]

        actual_output.seek(0)
        self.assertSequenceEqual(
            [line.rstrip()
             for line in actual_output.readlines()], expected_csv_data)

    def test_load_then_write_csv_data(self):
        csv_data = [
            'Num Shares,Symbol,Description,Buy Date,Adjusted Buy Date,Basis,'
            'Adjusted Basis,Sell Date,Proceeds,Adjustment Code,Adjustment,'
            'Form Position,Buy Lot,Replacement For,Is Replacement,'
            'Loss Processed',
            '10,ABC,A,09/15/2014,09/14/2014,2000,2100,10/05/2014,1800,W,200,'
            'form1,lot1,lot3|lot4,True,True',
            '10,ABC,A,09/15/2014,,2000,,10/05/2014,1800,W,200,form2,lot2,,,',
            '20,ABC,A,09/25/2014,,3000,,11/05/2014,1800,,,,_1,,,'
        ]
        lots = lots_lib.Lots.create_from_csv_data(csv_data)
        actual_output = io.StringIO()
        lots.write_csv_data(actual_output)
        actual_output.seek(0)
        self.assertSequenceEqual(
            [line.rstrip() for line in actual_output.readlines()], csv_data)

    def test_is_loss(self):
        loss_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                datetime.date(2014, 10, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)
        self.assertTrue(loss_lot.is_loss())

        gain_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 1000, 1000,
                                datetime.date(2014, 10, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)
        self.assertFalse(gain_lot.is_loss())

        unsold_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                  datetime.date(2014, 9, 15), 2000, 2000, None,
                                  0, '', 0, 'form1', 'lot1', [], True, False)
        self.assertFalse(unsold_lot.is_loss())

    def test_compare_by_buy_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 7),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 7),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        lots.sort(key=cmp_to_key(lots_lib.Lot.cmp_by_buy_date))
        self.assertTrue(lots == expected)

    def test_compare_by_original_buy_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 7), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 7), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        lots.sort(key=cmp_to_key(lots_lib.Lot.cmp_by_original_buy_date))
        self.assertTrue(lots == expected)

    def test_compare_by_sell_date(self):
        lots = []
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))

        expected = []
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 3),
            datetime.date(2014, 9, 3), 0, 0, datetime.date(2014, 10, 6), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(2, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        expected.append(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, None, 0, '', 0, 'form1', '', [],
            False, False))

        lots.sort(key=cmp_to_key(lots_lib.Lot.cmp_by_sell_date))
        self.assertTrue(lots == expected)

    def test_contents_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))
        self.assertTrue(lots.contents_equal(lots))

        other_lots = copy.deepcopy(lots)
        self.assertTrue(lots.contents_equal(other_lots))

    def test_contents_not_equal(self):
        lots = lots_lib.Lots([])
        lots.add(lots_lib.Lot(1, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form2', '', [], False, False))
        lots.add(lots_lib.Lot(5, '', '', datetime.date(2014, 9, 1),
            datetime.date(2014, 9, 1), 0, 0, datetime.date(2014, 10, 5), 0, '',
            0, 'form1', '', [], False, False))
        lots.add(lots_lib.Lot(3, '', '', datetime.date(2014, 9, 2),
            datetime.date(2014, 9, 2), 0, 0, datetime.date(2014, 11, 5), 0, '',
            0, 'form1', '', [], False, False))

        other_lots = copy.deepcopy(lots)
        other_lots.lots()[0].num_shares = 2
        self.assertFalse(lots.contents_equal(other_lots))

#%% Test tax-related calculations for a single lot
class TestLotGains(unittest.TestCase):
    def test_is_long_term(self):
        #Set today's date
        t = datetime.date(2022,5,22)
        
        #Test a long-term lot
        longterm_lot1 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                datetime.date(2022, 4, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertTrue(longterm_lot1.is_long_term(t))
        self.assertTrue(longterm_lot1.is_long_term())

        # Unsold lot 
        
        longterm_lot2 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                None, 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertTrue(longterm_lot2.is_long_term(t))
        self.assertFalse(longterm_lot2.is_long_term())


        #Test several short-term lots
        shortterm_lot1 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 2),
                                datetime.date(2021, 9, 15), 2000, 2200,
                                datetime.date(2022, 4, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertFalse(shortterm_lot1.is_long_term(t))
        self.assertFalse(shortterm_lot1.is_long_term())


        shortterm_lot2 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 2),
                                datetime.date(2021, 9, 15), 2000, 2200,
                                None, 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertFalse(shortterm_lot2.is_long_term(t))
        self.assertFalse(shortterm_lot2.is_long_term())

        # Test a lot that's exactly 1 year
        shortterm_lot3 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 2),
                                datetime.date(2021, 9, 15), 2000, 2200,
                                datetime.date(2022, 9, 15), 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertFalse(shortterm_lot3.is_long_term(t))
        self.assertFalse(shortterm_lot3.is_long_term())
        
        shortterm_lot4 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 2),
                                datetime.date(2021, 5, 22), 2000, 2200,
                                None, 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        self.assertFalse(shortterm_lot4.is_long_term(t))
        self.assertFalse(shortterm_lot4.is_long_term())
                
    def test_calc_gains(self):
    
        
        # set today's date and price
        t = datetime.date(2022,5,22)
        p = 100
        
        # =============================================================================
        # Testing long-term lots
        # =============================================================================
        # Test a realized long-term lot
        longterm_lot1 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                datetime.date(2016, 4, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        gains    = longterm_lot1.calc_gains()
        expected = (np.nan, -200, np.nan, np.nan)  #r_s, r_l, u_s, u_l
        self.assertTrue(test_dict_vs_vals(expected, gains))

        # Specify price and date    
        gains = longterm_lot1.calc_gains(t, p)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        #Test an unrealized long-term lot - specified proceeds, but no sell date
        longterm_lot2 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                None, 0, '', 0,
                                'form1', 'lot1', [], True, False)

        gains = longterm_lot2.calc_gains()
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        #Test an unrealized long-term lot - no proceeds or sell date
        longterm_lot3 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2014, 9, 15),
                                datetime.date(2014, 9, 15), 2000, 2000,
                                None, 0, '', 0,
                                'form1', 'lot1', [], True, False)

        # Specify price and date    
        gains = longterm_lot3.calc_gains(t, p)
        expected = (np.nan, np.nan, np.nan, -1000)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        # Specify price but not date    
        gains = longterm_lot3.calc_gains(price=p)
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))
        
        # =============================================================================
        # Testing short-term lots
        # =============================================================================
        # Test a realized short-term lot
        shortterm_lot1 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 15),
                                datetime.date(2021, 9, 15), 2000, 2000,
                                datetime.date(2022, 4, 5), 1800, '', 0,
                                'form1', 'lot1', [], True, False)

        gains = shortterm_lot1.calc_gains()
        expected = (-200, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        # Specify price and date    
        gains = shortterm_lot1.calc_gains(t, p)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        #Test an unrealized short-term lot - specified proceeds, but no sell date
        shortterm_lot2 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 15),
                                datetime.date(2021, 9, 15), 2000, 2000,
                                None, 0, '', 0,
                                'form1', 'lot1', [], True, False)

        gains = shortterm_lot2.calc_gains()
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        #Test an unrealized short-term lot - no proceeds or sell date
        shortterm_lot3 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 15),
                                datetime.date(2021, 9, 15), 2000, 2000,
                                None, 0, '', 0,
                                'form1', 'lot1', [], True, False)

        # Specify price and date    
        gains = shortterm_lot3.calc_gains(t, p)
        expected = (np.nan, np.nan, -1000, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        # Specify price but not date    
        gains = shortterm_lot3.calc_gains(price=p)
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))

        #Test an unrealized short-term lot - exactly 1 year from the adj buy date
        shortterm_lot4 = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 15),
                                datetime.date(2021, 5, 22), 2000, 2000,
                                None, 0, '', 0,
                                'form1', 'lot1', [], True, False)

        gains = shortterm_lot4.calc_gains(price=p)
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))
        
        # Test a washed lot
        washed_lot = lots_lib.Lot(10, 'ABC', 'A', datetime.date(2022, 1, 2),
                                datetime.date(2021, 5, 22), 2000, 2200,
                                None, 0, 'W', 0,
                                'form1', 'lot1', [], True, False)

        gains = washed_lot.calc_gains(price=p, date=t)
        expected = (np.nan, np.nan, np.nan, np.nan)
        self.assertTrue(test_dict_vs_vals(expected, gains))


#%%  Test functionalities for multiple lots
class TestLotsGains(unittest.TestCase):
   
    def test_calc_gain(self):
        """ Test calculations of gains for the lots portfolio """
        # Create a lot portfoio for a test
        lots_rows = []
        
        # Long-term Lots        
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15),
            datetime.date(2014, 9, 15), 2000, 2000,
            datetime.date(2016, 4, 5), 1800, '', 0,
            'form1', 'lot1', [], True, False))
        
        
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2014, 9, 15),
            datetime.date(2014, 9, 15), 2000, 2000,
            None, 0, '', 0,
            'form1', 'lot1', [], True, False))
        
        # # Short-term Lots
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2022, 1, 15),
            datetime.date(2021, 9, 15), 2000, 2000,
            datetime.date(2022, 4, 5), 1800, '', 0,
            'form1', 'lot1', [], True, False))
            
        lots_rows.append(lots_lib.Lot(
            10, 'ABC', 'A', datetime.date(2022, 1, 15),
            datetime.date(2021, 9, 15), 2000, 2000,
            None, 1800, '', 0,
            'form1', 'lot1', [], True, False))
            
        # lots_rows.append(lots_lib.Lot(
        #     10, 'ABC', 'A', datetime.date(2022, 1, 15),
        #     datetime.date(2021, 9, 15), 2000, 2000,
        #     None, None, '', 0,
        #     'form1', 'lot1', [], True, False))
        
        # lots_rows.append(lots_lib.Lot(
        #     10, 'ABC', 'A', datetime.date(2022, 1, 15),
        #     datetime.date(2021, 5, 22), 2000, 2000,
        #     None, None, '', 0,
        #     'form1', 'lot1', [], True, False))
        
        lots = lots_lib.Lots(lots_rows)        

         # set today's date and price
        t = datetime.date(2022,5,22)
        p = 100
         
        gains = lots.calc_gains(date = t, price=p)
        
        exp_per_lot = [ [np.nan,  -200,  np.nan, np.nan ],
                        [np.nan, np.nan, np.nan,  -1000 ],
                        [-200,   np.nan, np.nan, np.nan ], 
                        [np.nan, np.nan,  -1000, np.nan ]                        
                        ];

        expected = np.nansum(exp_per_lot,axis=0)
        expected = np.where(np.isnan(exp_per_lot).all(axis=0),np.nan, expected)
        self.assertTrue(test_dict_vs_vals(expected, gains))           

#%% Entry point
if __name__ == '__main__':
    unittest.main()
