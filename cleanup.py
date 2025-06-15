import os
import shutil
import sys

def clear_pycache(directory=None):
    """
    Remove all __pycache__ directories and .pyc files from the project
    
    Args:
        directory: The directory to clean (defaults to current directory)
    """
    if directory is None:
        directory = os.path.dirname(os.path.abspath(__file__))
    
    print(f"Cleaning Python cache files in: {directory}")
    
    # Counter for removed items
    removed_dirs = 0
    removed_files = 0
    
    # Walk through all directories
    for root, dirs, files in os.walk(directory):
        # Remove __pycache__ directories
        if '__pycache__' in dirs:
            cache_dir = os.path.join(root, '__pycache__')
            print(f"Removing: {cache_dir}")
            try:
                shutil.rmtree(cache_dir)
                removed_dirs += 1
            except Exception as e:
                print(f"Error removing {cache_dir}: {e}")
        
        # Remove .pyc files
        for file in files:
            if file.endswith('.pyc') or file.endswith('.pyo'):
                pyc_file = os.path.join(root, file)
                print(f"Removing: {pyc_file}")
                try:
                    os.remove(pyc_file)
                    removed_files += 1
                except Exception as e:
                    print(f"Error removing {pyc_file}: {e}")
    
    print(f"\nCleanup complete!")
    print(f"Removed {removed_dirs} __pycache__ directories")
    print(f"Removed {removed_files} .pyc/.pyo files")

if __name__ == "__main__":
    # If directory argument is provided, use it
    if len(sys.argv) > 1:
        clear_pycache(sys.argv[1])
    else:
        clear_pycache()
