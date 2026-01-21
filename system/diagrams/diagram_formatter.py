from typing import Optional


def format_diagram(diagram: str) -> str:
    if not diagram:
        return ""
    
    lines = [line.rstrip() for line in diagram.split('\n')]
    
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    
    return '\n'.join(lines)


def trim_diagram(diagram: str, max_width: Optional[int] = None) -> str:
    if not diagram:
        return ""
    
    if max_width is None:
        lines = diagram.split('\n')
        if lines:
            avg_line_len = sum(len(line) for line in lines) / len(lines)
            max_width = max(60, min(120, int(avg_line_len * 1.5)))
        else:
            max_width = 100
    
    lines = diagram.split('\n')
    trimmed_lines = []
    
    for line in lines:
        if len(line) > max_width:
            trimmed_lines.append(line[:max_width - 3] + "...")
        else:
            trimmed_lines.append(line)
    
    return '\n'.join(trimmed_lines)

