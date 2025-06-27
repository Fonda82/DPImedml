import os
import glob
import codecs

def fix_file_encoding(filepath):
    # First detect encoding
    with open(filepath, 'rb') as f:
        raw = f.read(4)
        
    if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
        print(f"Converting {os.path.basename(filepath)} from UTF-16 to UTF-8...")
        # Read the file as UTF-16
        with open(filepath, 'r', encoding='utf-16') as f:
            content = f.read()
            
        # Write it back as UTF-8 (without BOM)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"File {os.path.basename(filepath)} does not need conversion")
        return False

# Check all HTML files in the patients templates directory
template_path = 'templates/patients'
template_files = glob.glob(os.path.join(template_path, '*.html'))

converted_files = 0
for file_path in template_files:
    if fix_file_encoding(file_path):
        converted_files += 1

print(f"\nConverted {converted_files} files from UTF-16 to UTF-8") 