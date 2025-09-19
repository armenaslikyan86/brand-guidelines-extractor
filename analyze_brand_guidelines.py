"""Brand guidelines extractor CLI wrapper.

This module preserves the original entrypoint while delegating the heavy lifting
to the reusable :mod:`brand_guidelines_extractor` package.
"""

from brand_guidelines_extractor import main


if __name__ == "__main__":
    main()
