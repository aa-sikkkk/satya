"""
ASCII Diagram Library for Satya Learning System

Provides visual learning aids through text-based diagrams.
Essential for offline, text-only interface.
"""

from typing import Dict, Optional

class ASCIIDiagramLibrary:
    """
    Repository of educational ASCII diagrams.
    """
    
    def __init__(self):
        self._library = {
            # --- BIOLOGY ---
            "cell_plant": r"""
      _______________________
     /   Cell Wall           \
    |   ___________________   |
    |  /   Cell Membrane   \  |
    | |   (___________)     | |
    | |  (   Nucleus   )    | |
    | |   \___________/     | |
    | |      [Vacuole]      | |
    | | [Chloroplast]       | |
    | |_____________________| |
    \_______________________/
    """,
            "dna": r"""
       A---T
      G-----C
     T-------A
    C---------G
     A-------T
      G-----C
    """,
    
            # --- PHYSICS ---
            "circuit_series": r"""
    + [Battery] -
    |           |
    |           |
    +--[Bulb]--[Bulb]--+
    """,
    
            "circuit_parallel": r"""
       +--[Bulb]--+
       |          |
    +--+          +-- - [Battery] +
       |          |
       +--[Bulb]--+
    """,
            "atom": r"""
         e-
           \
      e-    ( P+ N0 )    e-
           /
         e-
    (Bohr Model: P=Proton, N=Neutron, e=Electron)
    """,
    
            # --- CHEMISTRY ---
            "periodic_table_skeleton": r"""
    H                                                  He
    Li Be                               B  C  N  O  F  Ne
    Na Mg                               Al Si P  S  Cl Ar
    K  Ca Sc Ti V Cr Mn Fe Co Ni Cu Zn Ga Ge As Se Br Kr
    """,

            # --- MATH ---
            "triangle_right": r"""
    |\
    | \  Hypotenuse
    |  \
    |___\
    Base
    """,
            "coordinate_plane": r"""
          ^ Y
          |
    - - - + - - - > X
          |
          |
    (Cartesian System)
    """
        }
        
        # Keywords mapping to diagrams for auto-detection
        self._keywords = {
            "plant cell": "cell_plant",
            "animal cell": "cell_plant", # Fallback approx
            "dna": "dna",
            "gene": "dna",
            "series circuit": "circuit_series",
            "parallel circuit": "circuit_parallel",
            "electric circuit": "circuit_series",
            "atom": "atom",
            "electron": "atom",
            "periodic table": "periodic_table_skeleton",
            "triangle": "triangle_right",
            "pythagoras": "triangle_right",
            "graph": "coordinate_plane",
            "coordinate": "coordinate_plane"
        }

    def get_diagram(self, key: str) -> Optional[str]:
        """Retrieve a specific diagram by key."""
        return self._library.get(key)

    def find_diagram_by_text(self, text: str) -> Optional[str]:
        """
        Auto-detect relevant diagram based on text keywords.
        Returns the first matching diagram found.
        """
        text_lower = text.lower()
        for keyword, diagram_key in self._keywords.items():
            if keyword in text_lower:
                return self._library.get(diagram_key)
        return None

    def list_available_diagrams(self) -> str:
        """Return a formatted list of all available diagrams."""
        return ", ".join(sorted(self._library.keys()))
