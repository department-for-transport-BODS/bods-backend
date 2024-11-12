"""
Description: Utility functions for boilerplate
"""


def get_file_size(file_):
    """
    Returns the size of a file-like object in bytes.

    This function seeks to the end of the file to get its size, which works for
    both regular files on disk and file-like objects (such as in-memory files).

    Note:
    - This function will not work with file objects that do not support seeking.
    - The file pointer will be reset to the beginning of the file after size calculation.

    Parameters:
        file_ (file-like object): A file or file-like object with support for `.seek()` and `.tell()`.

    Returns:
        int: Size of the file in bytes.
    """
    # Seek to the end of the file to get the size
    file_.seek(0, 2)
    size = file_.tell()

    # Reset file pointer to the beginning of the file
    file_.seek(0)

    return size
