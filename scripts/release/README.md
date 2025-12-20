# Satya Release Scripts

This directory contains scripts for building and running Satya on 4GB RAM, CPU-only systems.

## Quick Start

### Windows
```batch
# Run CLI version
run_cli.bat

# Run GUI version
run_gui.bat
```

### Linux/Mac
```bash
# Make scripts executable
chmod +x run_cli.sh run_gui.sh

# Run CLI version
./run_cli.sh

# Run GUI version
./run_gui.sh
```

## Building Offline Bundle

Create a ready-to-distribute bundle:

```bash
python scripts/release/build_offline_bundle.py
```

This creates:
- `dist/offline_bundle/` - Directory with all required files
- `dist/offline_bundle.zip` - Compressed archive for distribution

The bundle includes:
- Model files (GGUF format)
- ChromaDB vector database
- Educational content
- Documentation
- Launch scripts
- Requirements file

## Installation from Bundle

1. Extract `offline_bundle.zip` to a directory
2. Install Python 3.8+ if not already installed
3. Create virtual environment: `python -m venv venv`
4. Activate virtual environment:
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`
5. Install dependencies: `pip install -r requirements.txt`
6. Run using launcher scripts in `scripts/release/`




