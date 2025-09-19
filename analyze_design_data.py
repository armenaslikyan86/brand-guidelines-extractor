"""Design data analyzer CLI wrapper.

This module preserves the original entrypoint while delegating the heavy lifting
to the reusable :mod:`design_data_analyzer` package.
"""

from design_data_analyzer import main


if __name__ == "__main__":
    main()
