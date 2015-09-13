"""
File and path manipulation utility function(s)
"""
import os


def get_modified_fname(fname, ext, suffix='.'):
    """
    Change the name of provided filename to different. Suffix should contain
    dot, since it is last part of the filename and dot should separate it
    from extension. If not, dot will be added automatically.
    """
    path, _ = os.path.splitext(fname)
    if not (suffix.endswith(".") or ext.startswith(".")):
        ext = "." + ext
    return "".join([path, suffix, ext])
