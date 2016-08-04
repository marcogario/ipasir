# gcc ipasirpicosatglue.c -o ipasirpicosatglue.so -Ipicosat-961/ -DVERSION=\"961\" -lpicosat -Lpicosat-961 -shared -fPIC
# LD_LIBRARY_PATH=`pwd`/ipasir/sat/picosat961/picosat-961 python -i ipasir_cffi.py


from cffi import FFI
ffi = FFI()

ipasir_h = \
"""
const char * ipasir_signature ();
void * ipasir_init ();
void ipasir_release (void * solver);
void ipasir_add (void * solver, int lit_or_zero);
void ipasir_assume (void * solver, int lit);
int ipasir_solve (void * solver);
int ipasir_val (void * solver, int lit);
int ipasir_failed (void * solver, int lit);
void ipasir_set_terminate (void * solver, void * state, int (*terminate)(void * state));
"""

ffi.cdef(ipasir_h)
ipasir = ffi.dlopen("ipasir/sat/picosat961/ipasirpicosatglue.so")

# Call method from lib
sig = ipasir.ipasir_signature()
# This returns a char* convert in python string
ffi.string(sig)
