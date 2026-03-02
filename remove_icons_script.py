import os
import emoji

def remove_emojis_from_dir(directory):
    count = 0
    for root, dirs, files in os.walk(directory):
        if '.venv' in dirs: dirs.remove('.venv')
        if '.git' in dirs: dirs.remove('.git')
        if 'chroma_db' in dirs: dirs.remove('chroma_db')
        if '__pycache__' in dirs: dirs.remove('__pycache__')
        if 'node_modules' in dirs: dirs.remove('node_modules')
        
        for file in files:
            if file.endswith(('.py', '.html', '.css', '.js', '.ts', '.jsx', '.tsx')):
                filepath = os.path.join(root, file)
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    new_content = emoji.replace_emoji(content, replace='')
                    
                    if new_content != content:
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(new_content)
                        print(f"Removed emojis from {filepath}")
                        count += 1
                except Exception as e:
                    print(f"Error processing {filepath}: {e}")
    print(f"Total files updated: {count}")

if __name__ == "__main__":
    remove_emojis_from_dir(r'd:\hr-ai-agent-pure-vector')
