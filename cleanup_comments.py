#!/usr/bin/env python3
import os
import re
from pathlib import Path

def remove_python_comments(content):
    lines = content.split('\n')
    cleaned_lines = []
    in_docstring = False
    docstring_char = None
    
    for line in lines:
        stripped = line.lstrip()
        
        if not in_docstring:
            if stripped.startswith('"""') or stripped.startswith("'''"):
                docstring_char = stripped[:3]
                if stripped.count(docstring_char) >= 2:
                    continue
                else:
                    in_docstring = True
                    continue
            elif stripped.startswith('#'):
                continue
            else:
                line_without_comment = re.sub(r'\s*#.*$', '', line)
                if line_without_comment.strip() or not line_without_comment:
                    cleaned_lines.append(line_without_comment)
        else:
            if docstring_char in stripped:
                in_docstring = False
                continue
    
    result = '\n'.join(cleaned_lines)
    result = re.sub(r'\n\n\n+', '\n\n', result)
    return result.strip() + '\n'

def remove_ts_comments(content):
    content = re.sub(r'//.*?$', '', content, flags=re.MULTILINE)
    content = re.sub(r'/\*[\s\S]*?\*/', '', content)
    content = re.sub(r'\n\s*\n\s*\n+', '\n\n', content)
    return content.strip() + '\n'

def process_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        if file_path.suffix == '.py':
            cleaned = remove_python_comments(content)
        elif file_path.suffix in ['.ts', '.tsx', '.js', '.jsx']:
            cleaned = remove_ts_comments(content)
        else:
            return False
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(cleaned)
        
        print(f"✓ Cleaned: {file_path}")
        return True
    except Exception as e:
        print(f"✗ Error processing {file_path}: {e}")
        return False

def main():
    root = Path(__file__).parent
    
    patterns = [
        'backend/**/*.py',
        'frontend/src/**/*.ts',
        'frontend/src/**/*.tsx',
        'api/**/*.py'
    ]
    
    total = 0
    success = 0
    
    for pattern in patterns:
        for file_path in root.glob(pattern):
            if '__pycache__' in str(file_path) or 'node_modules' in str(file_path):
                continue
            total += 1
            if process_file(file_path):
                success += 1
    
    print(f"\n{'='*60}")
    print(f"Processed {success}/{total} files successfully")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()
