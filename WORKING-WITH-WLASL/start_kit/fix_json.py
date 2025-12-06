import os

file_path = 'start_kit/WLASL_subset.json'

def fix_json():
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read().strip()

    # If it's empty, make it an empty list
    if not content:
        content = "[]"
        
    else:
        # Wrap in brackets if not present
        if not content.startswith('['):
            content = '[\n' + content
        
        # Remove trailing comma if present (ignoring trailing whitespace which we stripped)
        if content.endswith(','):
             content = content[:-1]
             
        if not content.endswith(']'):
            content = content + '\n]'

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Fixed WLASL_subset.json format.")

if __name__ == "__main__":
    fix_json()
