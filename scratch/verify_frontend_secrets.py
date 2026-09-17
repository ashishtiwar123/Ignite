import os
import re

PATTERNS = [
    r'SUPABASE_KEY',
    r'SUPABASE_SERVICE_ROLE',
    r'service_role',
    r'GEMINI_API_KEY',
    r'VITE_SUPABASE',
    r'VITE_GEMINI',
    r'secret[_-]?key',
    r'service[_-]?role'
]

compiled = [re.compile(p, re.IGNORECASE) for p in PATTERNS]

found_leaks = []

for root, dirs, files in os.walk('frontend'):
    if 'node_modules' in root or '.git' in root or '.output' in root or 'dist' in root:
        continue
    for f in files:
        if f.endswith(('.ts', '.tsx', '.js', '.jsx', '.html', '.json', '.css', '.env', '.env.local')):
            path = os.path.join(root, f)
            try:
                with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                    for line_num, line in enumerate(handle, 1):
                        for pattern in compiled:
                            if pattern.search(line):
                                found_leaks.append((path, line_num, line.strip()))
            except Exception as e:
                print(f"Error reading {path}: {e}")

print(f"Total sensitive key matches found in frontend: {len(found_leaks)}")
for path, line_num, line in found_leaks:
    print(f"  {path}:{line_num} -> {line[:80]}")

if len(found_leaks) == 0:
    print("\nPASS: Zero backend credentials or secret references exist in frontend code!")
else:
    print("\nFAIL: Found potential leaks in frontend!")
