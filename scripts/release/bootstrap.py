"""
Bootstrap script for Nuitka.

"""

import os
import sys
import pathlib

bundle_dir = pathlib.Path(__file__).parent.resolve()

# Change working directory to the bundle directory
# This ensures all relative paths in the codebase resolve correctly
os.chdir(bundle_dir)


# Import the main_window module and run the application
from student_app.gui_app.main_window import NEBeduApp

if __name__ == "__main__":
    app = NEBeduApp()
    app.mainloop()

