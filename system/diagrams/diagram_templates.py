DIAGRAM_TEMPLATES = {
    "for_loop": """
┌─────────┐
│  Start  │
└────┬────┘
     │
┌────▼────┐
│ Get item│
└────┬────┘
     │
┌────▼────┐
│ Execute │
└────┬────┘
     │
┌────▼────┐
│  Next?  │
└──┬────┬─┘
Yes│    │No
   └────┘
     │
┌────▼────┐
│   End   │
└─────────┘
""".strip(),
    
    "while_loop": """
┌─────────┐
│  Start  │
└────┬────┘
     │
┌────▼────┐
│ Check   │
│Condition│
└──┬────┬─┘
True│    │False
    │    │
┌───▼──┐ └───┐
│ Body │     │
└───┬──┘     │
    │        │
    └────────┘
     │
┌────▼────┐
│   End   │
└─────────┘
""".strip(),
    
    "if_else": """
┌─────────┐
│  Start  │
└────┬────┘
     │
┌────▼────┐
│Condition│
└──┬────┬─┘
True│    │False
    │    │
┌───▼──┐ ┌───▼──┐
│  If  │ │ Else │
│ Block│ │ Block│
└───┬──┘ └───┬──┘
    │        │
    └───┬────┘
        │
┌───────▼───────┐
│   Continue    │
└───────────────┘
""".strip(),
    
    "process_3_steps": """
┌─────────────┐
│   Step 1    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Step 2    │
└──────┬──────┘
       │
┌──────▼──────┐
│   Step 3    │
└─────────────┘
""".strip(),
}


def get_template(template_name: str) -> str:
    """
    Get diagram template by name.
    
    Args:
        template_name: Name of the template
    
    Returns:
        Template diagram string or empty string if not found
    """
    return DIAGRAM_TEMPLATES.get(template_name, "")

