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