#!/usr/bin/env python3
"""
Build Standalone Executables for Satya Learning System - ENHANCED for rural deployment

This script uses PyInstaller to create standalone executables for both
the GUI and CLI versions of the application. The executables will not
require Python to be installed on the target system.

Usage:
    python scripts/release/build_executables.py [--gui-only] [--cli-only] [--clean] [--validate]
"""

import argparse
import subprocess
import sys
import shutil
from pathlib import Path
from typing import List, Optional


def check_and_fix_pathlib() -> bool:
    """Check for and remove obsolete pathlib package if present."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "show", "pathlib"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print("[!] Obsolete 'pathlib' package detected. Removing...")
            try:
                subprocess.run(
                    [sys.executable, "-m", "pip", "uninstall", "pathlib", "-y"],
                    check=True,
                    capture_output=True
                )
                print("[OK] Removed obsolete pathlib package")
                return True
            except subprocess.CalledProcessError:
                print("[ERROR] Failed to remove pathlib package. Please run: pip uninstall pathlib")
                return False
    except Exception:
        pass
    return True


def check_pyinstaller() -> bool:
    """Check if PyInstaller is installed."""
    if not check_and_fix_pathlib():
        return False
    
    try:
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", "--version"],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"[OK] PyInstaller found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("[!] PyInstaller not found. Installing...")
        try:
            subprocess.run(
                [sys.executable, "-m", "pip", "install", "pyinstaller"],
                check=True
            )
            print("[OK] PyInstaller installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("[ERROR] Failed to install PyInstaller")
            return False


def validate_rural_deployment_setup(project_root: Path) -> bool:
    """
    Validate that all required files are present for rural deployment.
    
    Args:
        project_root: Project root directory to validate
        
    Returns:
        True if setup is valid, False otherwise
    """
    print("\n[RURAL DEPLOYMENT VALIDATION]")
    print("="*50)
    
    # Check for model files
    model_path = project_root / "satya_data" / "models" / "phi_1_5"
    model_files = list(model_path.glob("*.gguf")) if model_path.exists() else []
    
    if not model_files:
        print(f"[ERROR] No GGUF model files found in: {model_path}")
        print("[HINT] Download Phi-1.5 GGUF from: https://huggingface.co/TheBloke/phi-1_5-GGUF")
        return False
    else:
        print(f"[OK] Found model files: {[f.name for f in model_files]}")
    
    # Check for ChromaDB
    chroma_path = project_root / "satya_data" / "chroma_db"
    if chroma_path.exists() and any(chroma_path.iterdir()):
        print(f"[OK] ChromaDB directory populated: {chroma_path}")
    else:
        print(f"[WARNING] ChromaDB directory empty or missing: {chroma_path}")
        print("[HINT] Run the embedding generation script first")
    
    # Check for content
    content_path = project_root / "scripts" / "data_collection" / "data" / "content"
    if content_path.exists() and any(content_path.iterdir()):
        print(f"[OK] Content directory populated: {content_path}")
    else:
        print(f"[ERROR] Content directory empty or missing: {content_path}")
        return False
    
    # Check for llama-cpp-python
    try:
        import llama_cpp
        print(f"[OK] llama-cpp-python is installed")
    except ImportError:
        print("[ERROR] llama-cpp-python is not installed")
        print("[HINT] Run: pip install llama-cpp-python")
        return False
    
    return True


def clean_build_dirs(project_root: Path) -> None:
    """Clean previous build directories."""
    dirs_to_clean = [
        project_root / "build",
        project_root / "dist",
    ]
    
    for dir_path in dirs_to_clean:
        if dir_path.exists():
            print(f"Cleaning {dir_path}...")
            shutil.rmtree(dir_path)
            print(f"✓ Cleaned {dir_path}")


def verify_project_structure(project_root: Path) -> bool:
    """
    Verify that the project structure is correct.
    
    Args:
        project_root: Project root directory to verify
        
    Returns:
        True if structure is valid, False otherwise
    """
    required_dirs = [
        "student_app",
        "satya_data",
        "scripts/release"
    ]
    
    required_files = [
        "student_app/main.py",
        "student_app/gui_app/main_window.py",
        "scripts/release/satya_gui.spec",
        "scripts/release/satya_cli.spec"
    ]
    
    missing = []
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            missing.append(f"Directory: {dir_path}")
    
    for file_path in required_files:
        if not (project_root / file_path).exists():
            missing.append(f"File: {file_path}")
    
    if missing:
        print("[ERROR] Project structure verification failed:")
        for item in missing:
            print(f"  - Missing {item}")
        print(f"\nProject root: {project_root}")
        print("Please ensure you're running the build script from the project root.")
        return False
    
    return True


def build_executable(spec_file: Path, project_root: Path) -> bool:
    """
    Build an executable using a PyInstaller spec file.
    
    Args:
        spec_file: Path to the .spec file
        project_root: Project root directory
        
    Returns:
        True if build succeeded, False otherwise
    """
    if not spec_file.exists():
        print(f"[ERROR] Spec file not found: {spec_file}")
        return False
    
    # Verify spec file is absolute or make it absolute
    if not spec_file.is_absolute():
        spec_file = project_root / spec_file
    
    print(f"\n{'='*60}")
    print(f"Building {spec_file.name}...")
    print(f"{'='*60}")
    print(f"Spec file: {spec_file}")
    print(f"Project root: {project_root}")
    
    try:
        # Change to project root for build
        result = subprocess.run(
            [sys.executable, "-m", "PyInstaller", str(spec_file.resolve()), "--clean", "--noconfirm"],
            cwd=project_root,
            check=True
        )
        print(f"[OK] Successfully built {spec_file.stem}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Failed to build {spec_file.stem}")
        print(f"Error details: {e}")
        return False


def create_distribution_package(project_root: Path, output_dir: Path) -> Optional[Path]:
    """
    Create a distribution package with executables and documentation.
    
    Args:
        project_root: Project root directory
        output_dir: Output directory for the package
        
    Returns:
        Path to the distribution package directory, or None if failed
    """
    dist_dir = project_root / "dist"
    if not dist_dir.exists():
        print("[ERROR] No dist directory found. Build executables first.")
        return None
    
    package_dir = output_dir / "Satya_Standalone"
    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n{'='*60}")
    print("Creating distribution package...")
    print(f"{'='*60}")
    
    # Copy executables
    gui_exe = dist_dir / "SatyaGUI.exe"
    cli_exe = dist_dir / "SatyaCLI.exe"
    
    if gui_exe.exists():
        shutil.copy2(gui_exe, package_dir / "SatyaGUI.exe")
        print(f"[OK] Copied {gui_exe.name}")
    else:
        print(f"[WARNING] GUI executable not found: {gui_exe}")
    
    if cli_exe.exists():
        shutil.copy2(cli_exe, package_dir / "SatyaCLI.exe")
        print(f"[OK] Copied {cli_exe.name}")
    else:
        print(f"[WARNING] CLI executable not found: {cli_exe}")
    
    # Create comprehensive rural deployment guide
    usage_guide = package_dir / "RURAL_DEPLOYMENT_GUIDE.txt"
    usage_guide.write_text("""
Satya Learning System - Rural Deployment Package
===============================================

This package contains standalone executables designed for offline use
in rural schools with limited hardware and internet connectivity.

FILES:
- SatyaGUI.exe: Graphical user interface version (recommended for students)
- SatyaCLI.exe: Command-line interface version (for teachers/tech support)

SYSTEM REQUIREMENTS:
- Windows 10 or later / Linux / macOS
- Minimum 4GB RAM (8GB recommended for better performance)
- At least 2GB free disk space
- No internet connection required after installation
- No Python installation required

INSTALLATION INSTRUCTIONS FOR RURAL SCHOOLS:
1. Copy this entire folder to the target computer (via USB drive)
2. Double-click SatyaGUI.exe to launch the graphical interface
3. No installation or internet needed - everything is self-contained

TROUBLESHOOTING FOR RURAL DEPLOYMENT:
- If "DLL not found" error: Install Visual C++ Redistributable
- If "Model not found": Ensure .gguf file is in satya_data/models/phi_1_5/
- If program crashes: Check available RAM (minimum 4GB required)
- For support: Contact your local tech coordinator

PERFORMANCE OPTIMIZATIONS:
- Uses lightweight Phi-1.5 model (under 1GB)
- Offline vector database for fast retrieval
- Compressed executables for smaller distribution size
- Optimized for low-resource environments

For technical support, please refer to the project documentation
or contact the development team.
""", encoding='utf-8')
    print("[OK] Created rural deployment guide")
    
    print(f"\n[OK] Distribution package created at: {package_dir}")
    return package_dir


def main() -> int:
    """Main build function."""
    parser = argparse.ArgumentParser(
        description="Build standalone executables for Satya Learning System"
    )
    parser.add_argument(
        "--gui-only",
        action="store_true",
        help="Build only the GUI executable"
    )
    parser.add_argument(
        "--cli-only",
        action="store_true",
        help="Build only the CLI executable"
    )
    parser.add_argument(
        "--clean",
        action="store_true",
        help="Clean build directories before building"
    )
    parser.add_argument(
        "--no-package",
        action="store_true",
        help="Skip creating distribution package"
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate rural deployment setup before building"
    )
    
    args = parser.parse_args()
    
    # Get project root
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    print("Satya Learning System - Executable Builder")
    print("=" * 60)
    print(f"Project root: {project_root}")
    
    # Validate rural deployment setup if requested
    if args.validate:
        if not validate_rural_deployment_setup(project_root):
            return 1
        if not args.gui_only and not args.cli_only:
            print("\n[OK] Rural deployment validation passed!")
            return 0
    
    # Verify project structure
    if not verify_project_structure(project_root):
        return 1
    
    # Check PyInstaller
    if not check_pyinstaller():
        return 1
    
    # Clean if requested
    if args.clean:
        clean_build_dirs(project_root)
    
    # Determine what to build
    build_gui = not args.cli_only
    build_cli = not args.gui_only
    
    # Build executables
    spec_dir = script_dir
    success_count = 0
    
    if build_gui:
        gui_spec = spec_dir / "satya_gui.spec"
        if build_executable(gui_spec, project_root):
            success_count += 1
    
    if build_cli:
        cli_spec = spec_dir / "satya_cli.spec"
        if build_executable(cli_spec, project_root):
            success_count += 1
    
    if success_count == 0:
        print("\n[ERROR] No executables were built successfully")
        return 1
    
    # Create distribution package
    if not args.no_package:
        output_dir = project_root / "dist"
        package_dir = create_distribution_package(project_root, output_dir)
        if package_dir:
            print(f"\n{'='*60}")
            print("BUILD COMPLETE!")
            print(f"{'='*60}")
            print(f"Executables are in: {project_root / 'dist'}")
            print(f"Distribution package: {package_dir}")
            print("\nYou can now distribute the 'Satya_Standalone' folder to rural schools.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())