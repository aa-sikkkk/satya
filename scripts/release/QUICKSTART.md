Satya - Install Guide for Students (Windows, fully offline)
============================================================

TWO RELEASE ZIPs - WHICH ONE DO YOU HAVE?
  Satya_Student_Offline_Win.zip   <- FULLY OFFLINE install (recommended)
  Satya_Student_Installer_Win.zip <- installer-only zip, needs internet
     once during "INSTALL" below (it downloads libraries from pip.org);
     use this only when the offline zip is too large to transfer.

WHAT YOU NEED FIRST (one-time, on any computer with internet):
  1. Python 3.12 (3.11 also works) - python.org/downloads
     IMPORTANT: tick "Add python.exe to PATH" during install.
  2. From the Satya Releases page, download BOTH:
       - Satya_Student_Offline_Win.zip      (app + libraries, ~2 GB)
       - Student Application + Phi 1.5 Model Download asset (the AI model)

INSTALL with Satya_Student_Offline_Win.zip (no internet needed):  1. Unzip Satya_Student_Offline_Win.zip anywhere (e.g. Desktop).
  2. Inside the unzipped folder, right-click install_satya.ps1
     -> Run with PowerShell.
     Say "A"/"Yes" if the system asks about scripts.
  3. A folder  %USERPROFILE%\Satya  is created containing everything.

ADD THE MODEL:
  Move the downloaded model folder so this path exists:
    %USERPROFILE%\Satya\satya_data\models\phi15

KNOWLEDGE BASE:
  The offline zip already contains the current question/answer knowledge
  base (auto-installed). NEW content released later arrives as
  'Satya_Knowledge_Base.zip' on the same Releases page - to update:
  unzip it anywhere, then copy the chroma_db folder from
  inside knowledge_base\ over   %USERPROFILE%\Satya\satya_data\chroma_db

START:
  Double-click   satya-gui.cmd   (graphical app)
  or             satya.cmd      (text/CLI app)

TROUBLESHOOTING:
  - "python not found": re-install Python, tick PATH checkbox.
  - Slow first launch: the app builds its question index once.
  - Wrong Python version: the app needs Python 3.11 or 3.12.
