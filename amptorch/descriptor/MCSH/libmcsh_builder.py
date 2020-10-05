import cffi

ffibuilder = cffi.FFI()
ffibuilder.cdef(
    """int calculate_atomistic_mcsh(double **, double **, double **, int*,
                                    int *, int, int*, int,
                                    int**, double **, int, double **, int*, int*, 
                                    double**, double**);
    """
)
ffibuilder.set_source(
    "amptorch.descriptor.MCSH._libmcsh",
    '#include "calculate_atomistic_mcsh.h"',
    sources=[
        "amptorch/descriptor/MCSH/calculate_atomistic_mcsh.cpp",
        "amptorch/descriptor/MCSH/atomistic_mcsh.cpp"
    ],
    source_extension=".cpp",
    include_dirs=["amptorch/descriptor/MCSH/"],
)

if __name__ == "__main__":
    ffibuilder.compile(verbose=True)
