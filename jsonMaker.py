import os
import json
import sys

def _safe_path_for_print(path):
    try:
        if sys.stdout.encoding:
            return path.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        else:
            return path.encode('ascii', errors='replace').decode('ascii')
    except Exception:
        return path.encode('ascii', errors='replace').decode('ascii')

def parse_song_ini(file_path):
    song_info = {}
    content = None
    # Try multiple encodings to handle special characters like 'Ö'
    for enc in ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']:
        try:
            with open(file_path, 'r', encoding=enc) as f:
                content = f.readlines()
            break 
        except (UnicodeDecodeError, UnicodeError):
            continue

    if content is None:
        print(f"SKIPPED: Encoding error on '{_safe_path_for_print(file_path)}'")
        return None

    for line in content:
        line = line.strip()
        if '=' in line:
            parts = line.split('=', 1)
            key = parts[0].strip().lower()
            value = parts[1].strip()
            
            if key == 'artist': song_info['artist'] = value
            elif key == 'name': song_info['name'] = value
            elif key == 'genre': song_info['genre'] = value
            elif key == 'year':
                try:
                    song_info['year'] = int(value[:4])
                except ValueError:
                    song_info['year'] = None
                    
    if not song_info.get('artist') and not song_info.get('name'):
        print(f"SKIPPED: No artist/name tags found in '{_safe_path_for_print(file_path)}'")
        return None
        
    return song_info

def generate_song_list_json(root_directory, output_json_file='songs.json'):
    all_songs = []
    
    if not os.path.isdir(root_directory):
        print(f"CRITICAL ERROR: The directory '{_safe_path_for_print(root_directory)}' does not exist.")
        return

    print(f"--- Starting Scan of: {_safe_path_for_print(root_directory)} ---")

    for dirpath, dirnames, filenames in os.walk(root_directory):
        for filename in filenames:
            # Skip the metadata file itself
            if filename.lower() == 'song.ini':
                song_ini_path = os.path.join(dirpath, filename)
                song_data = parse_song_ini(song_ini_path)
                if song_data:
                    all_songs.append(song_data)
                continue
                
            file_path = os.path.join(dirpath, filename)
            
            # IMPROVED LOGIC: 
            # 1. If it's an .sng file, we strip the extension.
            # 2. If it's anything else (including extensionless files), we check for the " - " pattern.
            
            if filename.lower().endswith('.sng'):
                base_name = os.path.splitext(filename)[0]
            else:
                base_name = filename # Handle extensionless or files with other/no extensions

            if ' - ' in base_name:
                parts = base_name.split(' - ', 1)
                all_songs.append({
                    'artist': parts[0].strip(),
                    'name': parts[1].strip(),
                    'year': None,
                    'genre': None
                })
            else:
                # Only print skip for actual .sng files or files that look like they 
                # were meant to be songs but missed the separator.
                if filename.lower().endswith('.sng'):
                    print(f"SKIPPED: .sng file '{_safe_path_for_print(file_path)}' missing ' - ' separator")

    if all_songs:
        try:
            # ensure_ascii=False ensures 'Ö' is saved correctly
            with open(output_json_file, 'w', encoding='utf-8') as f:
                json.dump(all_songs, f, indent=4, ensure_ascii=False)
            print(f"\nSUCCESS: Generated '{output_json_file}' with {len(all_songs)} songs.")
        except IOError as e:
            print(f"ERROR: Could not write the JSON file: {e}")
    else:
        print("\nRESULT: No valid song data found.")

if __name__ == "__main__":
    target_folder = 'Downloaded Songs' 
    generate_song_list_json(target_folder, 'songs.json')