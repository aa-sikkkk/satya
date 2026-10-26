Satya - Install Guide for Students (Windows, fully offline)
============================================================

WHAT YOU NEED FIRST (one-time, on any computer with internet):
  1. Python 3.12 (3.11 also works) - python.org/downloads
     IMPORTANT: tick "Add python.exe to PATH" during install.
  2. From the Satya Releases page, download BOTH:
       - Satya_Student_Offline_Win.zip      (app + libraries, ~2 GB)
       - Student Application + Phi 1.5 Model Download asset (the AI model)

INSTALL (no internet needed):
  1. Unzip Satya_Student_Offline_Win.zip anywhere (e.g. Desktop).
  2. Inside the unzipped folder, right-click install_satya.ps1
     -> Run with PowerShell.
     Say "A"/"Yes" if the system asks about scripts.
  3. A folder  %USERPROFILE%\Satya  is created containing everything.

ADD THE MODEL:
  Move the downloaded model folder so this path exists:
    %USERPROFILE%\Satya\satya_data\models\phi15

START:
  Double-click   satya-gui.cmd   (graphical app)
  or             satya.cmd      (text/CLI app)

TROUBLESHOOTING:
  - "python not found": re-install Python, tick PATH checkbox.
  - Slow first launch: the app builds its question index once.
  - Wrong Python version: the app needs Python 3.11 or 3.12.
