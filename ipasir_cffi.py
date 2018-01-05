import os
from cffi import FFI

# gcc ipasirpicosatglue.c -o ipasirpicosatglue.so -Ipicosat-961/ -DVERSION=\"961\" -lpicosat -Lpicosat-961 -shared -fPIC
# LD_LIBRARY_PATH=`pwd`/ipasir/sat/picosat961/picosat-961 python -i ipasir_cffi.py


IPASIR_H = \
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

SAT = 10
UNSAT = 20
INTERRUPTED = 0


class IpasirLib(object):
    """Generic wrapper for an IPASIR SAT Solver.

    This class provides a wrapper to the IPASIR library itself.  It
    exports all commands available in the IPASIR interface.  A nicer
    wrapper to the solver can be obtained by instantiating
    IpasirSolver with the method solver(), that is equivalent to doing:
       IpasirSolver(self.init(), self)
    """

    def __init__(self, solver_fname):
        if not os.path.exists(solver_fname):
            raise ValueError("Cannot find solver library! " +
                             "File %s does not exist." % solver_fname)
        self.ffi = FFI()
        self.ffi.cdef(IPASIR_H)
        self._lib = self.ffi.dlopen(solver_fname)

    def signature(self):
        """Return the name and the version of the SAT solving library."""
        sig = self._lib.ipasir_signature()
        return self.ffi.string(sig)  # Convert char* into Python String

    def init(self):
        """Construct a new solver and return a pointer to it.

        Use the returned object as the first parameter in each
        of the following functions.

        Required state: N/A
        State after: INPUT
        """
        return self._lib.ipasir_init()

    def release(self, solver):
        """Release the solver.

        All its resources and allocated memory (destructor). The
        solver pointer cannot be used for any purposes after this
        call.
        """
        self._lib.ipasir_release(solver)

    def add(self, solver, lit_or_zero):
        """Add the given literal into the currently added clause
           or finalize the clause with a 0.

        Clauses added this way cannot be removed. The addition of
        removable clauses can be simulated using activation literals
        and assumptions.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT
        Literals are encoded as (non-zero) integers as in the DIMACS
        formats.  They have to be smaller or equal to INT_MAX and
        strictly larger than INT_MIN (to avoid negation overflow).
        This applies to all the literal arguments in API functions.
        """
        self._lib.ipasir_add(solver, lit_or_zero)

    def assume(self, solver, lit):
        """Add an assumption for the next SAT search

        This applies to the next ipasir_solve call. After calling
        ipasir_solve all the previously added assumptions are cleared.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT
        """
        self._lib.ipasir_assume(solver, lit)

    def solve(self, solver):
        """Solve the formula under the specified assumptions.

        If the formula is satisfiable the function returns 10 and the
        state of the solver is changed to SAT.

        If the formula is unsatisfiable the function returns 20 and
        the state of the solver is changed to UNSAT.

        If the search is interrupted (see ipasir_set_terminate) the
        function returns 0 and the state of the solver remains INPUT.

        This function can be called in any defined state of the solver.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT or SAT or UNSAT
        """
        return self._lib.ipasir_solve(solver)

    def val(self, solver, lit):
        """Get the truth value of the given literal in the found satisfying
        assignment.

        Return 'lit' if True, '-lit' if False, and 0 if not important.

        This function can only be used if ipasir_solve has returned 10
        and no 'ipasir_add' nor 'ipasir_assume' has been called since
        then, i.e., the state of the solver is SAT.

        Required state: SAT
        State after: SAT
        """
        return self._lib.ipasir_val(solver, lit)

    def failed(self, solver, lit):
        """Check if the given assumption literal was used to prove the
        unsatisfiability of the formula under the assumptions
        used for the last SAT search.

        Return 1 if so, 0 otherwise.

        This function can only be used if ipasir_solve has returned 20
        and no ipasir_add or ipasir_assume has been called since then,
        i.e., the state of the solver is UNSAT.

        Required state: UNSAT
        State after: UNSAT
        """
        return self._lib.ipasir_failed(solver, lit)

    def set_terminate(self, solver, state, callback):
        """Set a callback function used to indicate a termination requirement
        to the solver.

        The solver will periodically call this function and check its
        return value during the search. The ipasir_set_terminate
        function can be called in any state of the solver, the state
        remains unchanged after the call.

        The callback function is of the form "int terminate(void * state)"
        - it returns a non-zero value if the solver should terminate.
        - the solver calls the callback function with the parameter "state"

        having the value passed in the ipasir_set_terminate function
        (2nd parameter).

        Required state: INPUT or SAT or UNSAT
        State after: INPUT or SAT or UNSAT
        """
        c_callback = self.ffi.callback("int(*)(void *)")(callback)
        return self._lib.ipasir_set_terminate(solver, state, c_callback)

    def solver(self):
        """Returns a wrapped instance of the solver.

        !!! THIS IS NOT PART OF THE IPASIR INTERFACE !!!
        This method provides a more pythonic interface to the Library
        """
        return IpasirSolver(solver_obj=self.init(), ipasir_lib=self)


class IpasirSolver(object):
    """IPASIR SAT Solver.

       The solver implements all the methods of the IPASIR interface
       on a given solver instance.
    """

    def __init__(self, solver_obj, ipasir_lib):
        self._solver = solver_obj # C-Pointer to the IPASIR object
        self._lib = ipasir_lib

    def release(self):
        """Release the solver.

        All its resources and allocated memory (destructor). The
        solver pointer cannot be used for any purposes after this
        call.
        """
        return self._lib.release(self._solver)

    def add(self, lit_or_zero):
        """Add the given literal into the currently added clause
           or finalize the clause with a 0.

        Clauses added this way cannot be removed. The addition of
        removable clauses can be simulated using activation literals
        and assumptions.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT
        Literals are encoded as (non-zero) integers as in the DIMACS
        formats.  They have to be smaller or equal to INT_MAX and
        strictly larger than INT_MIN (to avoid negation overflow).
        This applies to all the literal arguments in API functions.
        """
        return self._lib.add(self._solver, lit_or_zero)

    def assume(self, lit):
        """Add an assumption for the next SAT search

        This applies to the next ipasir_solve call. After calling
        ipasir_solve all the previously added assumptions are cleared.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT
        """
        return self._lib.assume(self._solver, lit)

    def solve(self):
        """Solve the formula under the specified assumptions.

        If the formula is satisfiable the function returns 10 and the
        state of the solver is changed to SAT.

        If the formula is unsatisfiable the function returns 20 and
        the state of the solver is changed to UNSAT.

        If the search is interrupted (see ipasir_set_terminate) the
        function returns 0 and the state of the solver remains INPUT.

        This function can be called in any defined state of the solver.

        Required state: INPUT or SAT or UNSAT
        State after: INPUT or SAT or UNSAT
        """
        return self._lib.solve(self._solver)

    def val(self, lit):
        """Get the truth value of the given literal in the found satisfying
        assignment.

        Return 'lit' if True, '-lit' if False, and 0 if not important.

        This function can only be used if ipasir_solve has returned 10
        and no 'ipasir_add' nor 'ipasir_assume' has been called since
        then, i.e., the state of the solver is SAT.

        Required state: SAT
        State after: SAT
        """
        return self._lib.val(self._solver, lit)

    def failed(self, lit):
        """Check if the given assumption literal was used to prove the
        unsatisfiability of the formula under the assumptions
        used for the last SAT search.

        Return 1 if so, 0 otherwise.

        This function can only be used if ipasir_solve has returned 20
        and no ipasir_add or ipasir_assume has been called since then,
        i.e., the state of the solver is UNSAT.

        Required state: UNSAT
        State after: UNSAT
        """
        return self._lib.failed(self._solver, lit)

    def set_terminate(self, state, callback):
        """Set a callback function used to indicate a termination requirement
        to the solver.

        The solver will periodically call this function and check its
        return value during the search. The ipasir_set_terminate
        function can be called in any state of the solver, the state
        remains unchanged after the call.

        The callback function is of the form "int terminate(void * state)"
        - it returns a non-zero value if the solver should terminate.
        - the solver calls the callback function with the parameter "state"

        having the value passed in the ipasir_set_terminate function
        (2nd parameter).

        Required state: INPUT or SAT or UNSAT
        State after: INPUT or SAT or UNSAT
        """
        return self._lib.set_terminate(self._solver, state, callback)

    def __del__(self):
        self.release()


if __name__ == "__main__":
    lib = IpasirLib("ipasir/sat/picosat961/ipasirpicosatglue.so")
    solver1 = lib.solver()
    solver2 = lib.solver()

    # We can create multiple instances of the same solver
    print(solver1._solver)
    print(solver2._solver)
    del solver2

    # Add problem: (a \/ b) /\ (!a \/ b)
    solver1.add(1); solver1.add(2); solver1.add(0)
    solver1.add(-1); solver1.add(2); solver1.add(0)

    res = solver1.solve()
    assert res == SAT

    val_a = (solver1.val(1) == 1)
    val_b = (solver1.val(2) == 2)
    print(val_a, val_b)

    solver1.assume(-2) # Assume !b
    res = solver1.solve()
    assert res == UNSAT

    res = solver1.failed(2)
    assert res == 1

    #Assumptions are cleared after the call to solve
    res = solver1.solve()
    assert res == SAT

    def hello_cb(state):
        print("Hello %d" % state)
        return 0

    solver1.set_terminate("world", hello_cb)
    solver1.solve()


##
##  IPASIR LICENSE
##
# This LICENSE applies to all software included in the IPASIR distribution,
# except for those parts in sub-directories or in included software
# distribution packages, such as tar and zip files, which have their own
# license restrictions.  Those license restrictions are usually listed in the
# corresponding LICENSE or COPYING files, either in the sub-directory or in
# the included software distribution package (the tar or zip file).  Please
# refer to those licenses for rights to use that software.

# Copyright (c) 2014, Tomas Balyo, Karlsruhe Institute of Technology.
# Copyright (c) 2014, Armin Biere, Johannes Kepler University.

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to
# deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
# sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
# IN THE SOFTWARE.
