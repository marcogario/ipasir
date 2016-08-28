import bz2

def open_(fname):
    """Transparently handle .bz2 files."""
    if fname.endswith(".bz2"):
        return bz2.open(fname, "rt")
    return open(fname)


# Read dimacs problem
def read_dimacs(fname):
    prob_type, vars_cnt, clauses_cnt = None, None, None
    comments = []
    clauses = []

    with open_(fname) as fin:
        for line in fin:
            if line[0] == "c":
                comments.append(line)
            elif line[0] == "p":
                _, prob_type, vars_cnt, clauses_cnt = line.split(" ")
                prob_type = prob_type.strip()
                if prob_type != "cnf":
                    raise ValueError("File does not contain a cnf")
                vars_cnt = int(vars_cnt.strip())
                clauses_cnt = int(clauses_cnt)
                break

        for line in fin:
            if line[0] == "c":
                comments.append(line)
            else:
                cl = line.split(" ")
                assert cl[-1].strip() == "0", cl
                clauses.append([int(lit) for lit in cl[:-1]])

    # Validation (TODO)
    # - Clauses match the numer defined
    # - No variable above var_cnt
    return vars_cnt, clauses_cnt, clauses, comments

if __name__ == "__main__":
    import sys
    print(read_dimacs(sys.argv[1]))
