To create a .whl file for deployment do the following:
from the root directory of this project:
`python setup_operation.py bdist_wheel`

This creates a whl file containing the operation and its dependencies.
Furthermore, it contains a main file that can start the low_level_driver_server