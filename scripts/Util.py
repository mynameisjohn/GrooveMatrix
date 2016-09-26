# UI gap
class Constants:
    nGap = 10

# Used to construct ctypes sdl2 object
# from pointer to object in C++
import ctypes
def ctype_from_addr(capsule, type):
    ctypes.pythonapi.PyCapsule_GetPointer.restype = ctypes.c_void_p
    ctypes.pythonapi.PyCapsule_GetPointer.argtypes = [ctypes.py_object, ctypes.c_char_p]
    addr = ctypes.pythonapi.PyCapsule_GetPointer(capsule, None)
    if (addr != 0):
        return type.from_address(addr)
    raise RuntimeError('Error constructing ctype object, invalid capsule address')
