# Copyright (C) 2026 Aashik
#
# This software is subject to the terms of the PolyForm Noncommercial License 1.0.0.
# A copy of the license can be found in the LICENSE file or at 
# https://polyformproject.org/licenses/noncommercial/1.0.0/
#
# USE OF THIS SOFTWARE FOR COMMERCIAL PURPOSES IS STRICTLY PROHIBITED.

"""
ASCII Diagram Templates 
Standardized templates for common logic structures.
"""

DIAGRAM_TEMPLATES = {
    "for_loop": """
┌─────────────┐
│    START    │
└──────┬──────┘
       │
┌──────▼──────┐
│  GET ITEM   │
└──────┬──────┘
       │
┌──────▼──────┐
│ EXECUTE BODY│
└──────┬──────┘
       │
┌──────▼──────┐
│  HAS NEXT?  │
└──┬───────┬──┘
 YES│       │NO
    └───────┤
            │
      ┌─────▼─────┐
      │    END    │
      └───────────┘
""".strip(),
    
    "while_loop": """
┌─────────────┐
│    START    │
└──────┬──────┘
       │
┌──────▼──────┐
│  CONDITION  │
└──┬───────┬──┘
 TRUE│      │FALSE
     │      │
┌────▼───┐  │
│  BODY  │  │
└────┬───┘  │
     │      │
     └──────┤
            ▼
      ┌───────────┐
      │    END    │
      └───────────┘
""".strip(),
    
    "if_else": """
┌─────────────┐
│    START    │
└──────┬──────┘
       │
┌──────▼──────┐
│  CONDITION  │
└──┬───────┬──┘
 TRUE│      │FALSE
     │      │
┌────▼───┐ ┌────▼───┐
│   IF   │ │  ELSE  │
│ BLOCK  │ │ BLOCK  │
└────┬───┘ └────┬───┘
     │          │
     └────┬─────┘
          │
    ┌─────▼─────┐
    │ CONTINUE  │
    └───────────┘
""".strip(),
    
    "process_3_steps": """
┌─────────────┐
│   STEP 1    │
└──────┬──────┘
       │
┌──────▼──────┐
│   STEP 2    │
└──────┬──────┘
       │
┌──────▼──────┐
│   STEP 3    │
└─────────────┘
""".strip(),
}


def get_template(template_name: str, fill_data: dict = None) -> str:
    """
    Get diagram template by name and optionally fill it with data.
    
    Example fill_data: {"CONDITION": "User Valid?", "STEP 1": "Login"}
    """
    template = DIAGRAM_TEMPLATES.get(template_name, "")
    
    if not fill_data or not template:
        return template

    # If fill_data has "CONDITION": "Is Valid?", it replaces "CONDITION" in the ASCII
    for key, value in fill_data.items():
        if key in template:
            template = template.replace(key, value.center(len(key)))
    return template