import unittest
from example_package_YOUR_PACKAGE_NAME_HERE.example_package_YOUR_PACKAGE_NAME_HERE import example_package_YOUR_PACKAGE_NAME_HERE

class Test(unittest.TestCase):

    def test_empty_test(self):
        package = example_package_YOUR_PACKAGE_NAME_HERE()
        package.print_hello_world()
        self.assertTrue(True)

if __name__ == '__main__':
    unittest.main()