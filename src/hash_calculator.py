import hashlib
import os

def calculate(file, algorithm='sha256'):
    """
    Calculates the hash of a file, reading it in blocks to efficiently handle large files.

    Args:
        file (str): The full path to the file.
        algorithm (str): The hash algorithm to use (e.g., 'sha256', 'sha512').

    Returns:
        str or None: The hexadecimal hash of the file, or None if the file is not found.
    """
    
    if not os.path.exists(file):
        print(f"Error: File not found at path: {file}")
        return None

    try:
        hash_obj = hashlib.new(algorithm)
    except ValueError:
        print(f"Error: Hash algorithm '{algorithm}' not supported.")
        return None
    
    block_size = 65536 

    try:
        with open(file, 'rb') as f:
            while True:
                block = f.read(block_size)
                
                if not block:
                    break
                
                hash_obj.update(block)
    except IOError as e:
        print(f"Error reading the file: {e}")
        return None

    return hash_obj.hexdigest()

if __name__ == "__main__":
    
    file_to_analyze = 'requirements.txt'     
    algorithms = ['sha256', 'md5'] 

    print(f"Analyzing file: {file_to_analyze}\n")
    
    for algo in algorithms:
        file_hash = calculate(file_to_analyze, algo)
        
        if file_hash:
            print(f"  {algo.upper()} Hash: {file_hash}")
