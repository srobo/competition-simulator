import sys

# Provide a nicer check that the user has the right version of Python than
# them getting a `SyntaxError`
assert sys.version_info == (3, 7), (
    "Sorry, you must be using Python version 3.7. "
    "Please see the SR docs for how to switch your Python version."
)
