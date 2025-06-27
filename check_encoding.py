import os
import glob

def check_file_encoding(filepath):
    with open(filepath, 'rb') as f:
        raw = f.read(4)  # Read first 4 bytes
        if raw.startswith(b'\xff\xfe') or raw.startswith(b'\xfe\xff'):
            return f"UTF-16 BOM detected: {raw.hex()}"
        elif raw.startswith(b'\xef\xbb\xbf'):
            return f"UTF-8 BOM detected: {raw.hex()}"
        else:
            return f"No BOM detected: {raw[:4].hex()}"

# Check all HTML files in the patients templates directory
template_path = 'templates/patients'
template_files = glob.glob(os.path.join(template_path, '*.html'))

for file_path in template_files:
    encoding_result = check_file_encoding(file_path)
    print(f"{os.path.basename(file_path)}: {encoding_result}") 