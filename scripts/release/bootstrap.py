# Copyright (C) 2026 Aashik
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

"""
Bootstrap script for Nuitka
"""

import os
import sys
import pathlib
import traceback
import ctypes

log_file = pathlib.Path(os.getcwd()) / "satya_startup_error.log"

def show_error(msg):
    try:
        ctypes.windll.user32.MessageBoxW(0, str(msg), "Satya Startup Error", 0x10 | 0x1000)  # MB_ICONERROR | MB_SYSTEMMODAL
    except Exception:
        pass  
try:
    if "NUITKA_ONEFILE_PARENT" in os.environ:
        app_dir = pathlib.Path(os.environ["NUITKA_ONEFILE_PARENT"]).resolve()
    elif getattr(sys, 'frozen', False):
        app_dir = pathlib.Path(sys.executable).parent.resolve()
    else:
        app_dir = pathlib.Path(__file__).parent.resolve()

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"--- Satya Startup {sys.version} ---\n")
        f.write(f"sys.executable: {sys.executable}\n")
        f.write(f"__file__: {__file__ if '__file__' in globals() else 'N/A'}\n")
        f.write(f"NUITKA_ONEFILE_PARENT: {os.environ.get('NUITKA_ONEFILE_PARENT', 'Not set')}\n")
        f.write(f"Detected app_dir: {app_dir}\n")
        f.write(f"Current CWD before: {os.getcwd()}\n")
        f.write(f"Files in app_dir: {list(app_dir.glob('*'))}\n")
        f.write(f"satya_data exists: {(app_dir / 'satya_data').exists()}\n\n")

    os.chdir(app_dir)

    from student_app.gui_app.main_window import NEBeduApp

    if __name__ == "__main__":
        app = NEBeduApp()
        app.mainloop()

except Exception as e:
    error_msg = f"Startup failed!\n\nError: {e}\n\nSee log: {log_file}\n\n{traceback.format_exc()}"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(f"CRASH at {os.getcwd()}: {error_msg}\n")
    show_error(error_msg)
    sys.exit(1)


