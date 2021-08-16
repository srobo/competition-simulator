import sys

# Provide a nicer check that the user has the right version of Python than
# them getting a `SyntaxError`
assert sys.version_info >= (3, 7), (
    "Sorry, you must be using a recent version of Python 3. "
    "Please see the SR docs for how to switch your Python version."
)
