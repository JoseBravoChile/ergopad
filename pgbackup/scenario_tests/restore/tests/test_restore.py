import unittest
from utils.utils import DBConnection


class TestRestore(unittest.TestCase):

    def setUp(self):
        self.db = DBConnection()

    def test_read_data(self):
        # create new table
        self.db.conn.autocommit = True
        with self.db.cursor() as c:
            c.execute(
                """
                SELECT * FROM restore_test;
                """
            )

            rows = c.fetchall()
            self.assertEqual(len(rows), 1)
