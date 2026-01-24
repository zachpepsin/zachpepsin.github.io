import os
import json
import sys # Import sys to access sys.stdout.encoding

def _safe_path_for_print(path):
    """
    Encodes a path string to be safely printable to consoles that might not
    support all Unicode characters. Replaces unencodable characters with '?'.
    """
    try:
        # Attempt to encode using the default console encoding and then decode back.
        # This will replace unencodable characters with a safe representation.
        # sys.stdout.encoding gets the encoding used by the console.
        if sys.stdout.encoding:
            return path.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
        else:
            # Fallback if sys.stdout.encoding is None (e.g., redirected output)
            return path.encode('ascii', errors='replace').decode('ascii')
    except Exception:
        # Catch any other encoding or decoding errors, fallback to ASCII replacement
        return path.encode('ascii', errors='replace').decode('ascii')


def parse_song_ini(file_path):
    """
    Parses a 'song.ini' file and extracts artist, name, year, and genre.

    Args:
        file_path (str): The full path to the song.ini file.

    Returns:
        dict: A dictionary containing 'artist', 'name', 'year', and 'genre'
              if found, otherwise an empty dictionary or a dictionary with
              only the found fields. Returns None if the file cannot be read.
    """
    song_info = {}
    try:
        # Use 'errors=ignore' for encoding issues, as ini files can sometimes be
        # in various encodings. This prevents crashes due to character decoding.
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                line = line.strip()
                if line.startswith('artist ='):
                    song_info['artist'] = line.split('=', 1)[1].strip()
                elif line.startswith('name ='):
                    song_info['name'] = line.split('=', 1)[1].strip()
                elif line.startswith('year ='):
                    try:
                        song_info['year'] = int(line.split('=', 1)[1].strip())
                    except ValueError:
                        # If year cannot be parsed as an integer, set to None and print warning
                        print(f"Warning: Could not parse year in '{_safe_path_for_print(file_path)}'. Value found: '{line.split('=', 1)[1].strip()}'. Setting year to None.")
                        song_info['year'] = None
                elif line.startswith('genre ='):
                    song_info['genre'] = line.split('=', 1)[1].strip()
        return song_info
    except IOError as e:
        # Catch specific IOError for issues like file not found, permission denied
        print(f"Error reading file '{_safe_path_for_print(file_path)}': {e}. Skipping this file.")
        return None
    except Exception as e:
        # Catch any other unexpected errors during file parsing
        print(f"An unexpected error occurred while processing '{_safe_path_for_print(file_path)}': {e}. Skipping this file.")
        return None

def generate_song_list_json(root_directory, output_json_file='songs.json'):
    """
    Scans a root directory for subfolders containing 'song.ini' or '.sng' files,
    parses them, and generates a JSON file with a list of songs.

    Args:
        root_directory (str): The path to the directory to start scanning from.
        output_json_file (str): The name of the output JSON file.
    """
    all_songs = []
    
    # Ensure the root directory exists
    if not os.path.isdir(root_directory):
        print(f"Error: Root directory '{_safe_path_for_print(root_directory)}' not found. Please provide a valid path.")
        return

    print(f"Scanning directory: {_safe_path_for_print(root_directory)}")

    # Walk through the root directory and its subdirectories
    for dirpath, dirnames, filenames in os.walk(root_directory):
        # Process song.ini files
        if 'song.ini' in filenames:
            try:
                song_ini_path = os.path.join(dirpath, 'song.ini')
                print(f"Attempting to process song.ini at: {_safe_path_for_print(song_ini_path)}")
                
                song_data = parse_song_ini(song_ini_path)
                if song_data:
                    all_songs.append(song_data)
                else:
                    print(f"Skipping song.ini at '{_safe_path_for_print(song_ini_path)}' due to parsing issues or empty data.")
            except (OSError, ValueError) as e:
                print(f"Error processing path or file '{_safe_path_for_print(os.path.join(dirpath, 'song.ini'))}': {e}. Skipping this folder.")
            except Exception as e:
                print(f"An unexpected error occurred while scanning '{_safe_path_for_print(dirpath)}' for song.ini: {e}. Skipping this folder.")

        # Process .sng files
        for filename in filenames:
            if filename.lower().endswith('.sng'):
                sng_file_path = os.path.join(dirpath, filename)
                try:
                    # Expected format: "Artist Name - Song Name.sng"
                    base_name = os.path.splitext(filename)[0] # Get "Artist Name - Song Name"
                    
                    if ' - ' in base_name:
                        parts = base_name.split(' - ', 1) # Split only on the first ' - '
                        artist = parts[0].strip()
                        song_name = parts[1].strip()
                        
                        sng_song_data = {
                            'artist': artist,
                            'name': song_name,
                            'year': None, # Not available for .sng files
                            'genre': None  # Not available for .sng files
                        }
                        all_songs.append(sng_song_data)
                        print(f"Processed .sng file: {_safe_path_for_print(sng_file_path)}")
                    else:
                        print(f"Warning: .sng file '{_safe_path_for_print(sng_file_path)}' does not match 'Artist - Song' format. Skipping.")
                except Exception as e:
                    print(f"Error processing .sng file '{_safe_path_for_print(sng_file_path)}': {e}. Skipping this file.")
            
    # Write the collected song data to a JSON file
    if not all_songs:
        print("\nNo song data collected. Output JSON file will not be created.")
        return

    try:
        with open(output_json_file, 'w', encoding='utf-8') as f:
            json.dump(all_songs, f, indent=4, ensure_ascii=False)
        print(f"\nSuccessfully generated '{output_json_file}' with {len(all_songs)} songs.")
    except IOError as e:
        print(f"Error writing JSON file '{output_json_file}': {e}.")

if __name__ == "__main__":
    # --- Example Usage ---
    # Create a dummy directory structure and song.ini files for demonstration
    temp_dir = 'Downloaded Songs 20250919'
    # os.makedirs(os.path.join(temp_dir, 'Artist1', 'SongA'), exist_ok=True)
    # os.makedirs(os.path.join(temp_dir, 'Artist2', 'SongB'), exist_ok=True)
    # os.makedirs(os.path.join(temp_dir, 'Artist3', 'SongC'), exist_ok=True)
    # os.makedirs(os.path.join(temp_dir, 'Artist4', 'SongD_NoYear'), exist_ok=True) # For testing missing/bad year
    # os.makedirs(os.path.join(temp_dir, 'SngSongs'), exist_ok=True) # Directory for .sng files
    
    # # Create dummy song.ini files (as in previous versions)
    # with open(os.path.join(temp_dir, 'Artist1', 'SongA', 'song.ini'), 'w', encoding='utf-8') as f:
        # f.write("artist = AC/DC\n")
        # f.write("name = Back in Black\n")
        # f.write("year = 1980\n")
        # f.write("genre = Rock\n")
        # f.write("other_setting = 1\n")

    # with open(os.path.join(temp_dir, 'Artist2', 'SongB', 'song.ini'), 'w', encoding='utf-8') as f:
        # f.write("name = Bohemian Rhapsody\n")
        # f.write("artist = Queen\n")
        # f.write("genre = Classic Rock\n")
        # f.write("year = 1975\n")

    # with open(os.path.join(temp_dir, 'Artist3', 'SongC', 'song.ini'), 'w', encoding='utf-8') as f:
        # f.write("artist = Taylor Swift\n")
        # f.write("name = Love Story\n")
        # f.write("year = 2008\n")
        # f.write("genre = Pop\n")

    # with open(os.path.join(temp_dir, 'Artist4', 'SongD_NoYear', 'song.ini'), 'w', encoding='utf-8') as f:
        # f.write("artist = Example Artist\n")
        # f.write("name = Song with no year\n")
        # f.write("genre = Experimental\n")
        # f.write("year = NOT_A_YEAR\n")

    # # Create dummy .sng files
    # with open(os.path.join(temp_dir, 'SngSongs', 'Metallica - Enter Sandman.sng'), 'w') as f:
        # f.write("dummy content") # .sng files contents are ignored, only filename matters

    # with open(os.path.join(temp_dir, 'SngSongs', 'Foo Fighters - Everlong.sng'), 'w') as f:
        # f.write("dummy content")

    # with open(os.path.join(temp_dir, 'SngSongs', 'Malformed Name.sng'), 'w') as f: # To test malformed names
        # f.write("dummy content")


    # Call the function with the dummy directory
    generate_song_list_json(temp_dir, 'songs.json')

    # Optional: Clean up the dummy directory after execution
    # import shutil
    # shutil.rmtree(temp_dir)
    # print(f"Cleaned up dummy directory: {temp_dir}")
