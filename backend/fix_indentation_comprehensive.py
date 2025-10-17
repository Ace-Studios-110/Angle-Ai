#!/usr/bin/env python3
"""
Comprehensive indentation fix for angel_service.py
"""

import re

def fix_indentation_comprehensive():
    file_path = "/Users/mac/Desktop/Ahmed Work/Angle-Ai/backend/services/angel_service.py"
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    # Fix specific indentation issues
    fixes_applied = 0
    
    for i, line in enumerate(lines):
        line_num = i + 1
        original_line = line
        
        # Fix business context section indentation issues
        if line_num >= 3150 and line_num <= 3250:
            # Fix lines that should be indented for if blocks
            if (line.strip().startswith('business_context[') or 
                line.strip().startswith('context_weights[') or
                line.strip().startswith('print(f"🔍 DEBUG')) and not line.startswith('                            '):
                
                # Check if this should be indented based on previous lines
                if i > 0 and lines[i-1].strip().endswith(':'):
                    lines[i] = '                            ' + line.lstrip()
                    fixes_applied += 1
                    print(f"Fixed line {line_num}: {original_line.strip()[:50]}...")
        
        # Fix specific known problematic lines
        elif line_num in [3186, 3187, 3238, 3239]:
            if not line.startswith('                            '):
                lines[i] = '                            ' + line.lstrip()
                fixes_applied += 1
                print(f"Fixed line {line_num}: {original_line.strip()[:50]}...")
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(lines)
    
    print(f"✅ Applied {fixes_applied} indentation fixes!")

if __name__ == "__main__":
    fix_indentation_comprehensive()
