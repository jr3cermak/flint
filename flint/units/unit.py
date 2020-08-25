from flint.construct import Construct
from flint.report import Report
from flint.variable import Variable
from flint.document import is_docstring, Document


class Unit(object):
    unit_types = [
        'program',
        'function',
        'subroutine',
        'module',
        'submodule',
        'block',
        # Not really a program unit, but seems to work...
        'interface',
        'type',
        'enum',
    ]

    # R507 access-spec
    access_specs = [
        'public',
        'private',
    ]

    # R502 attr-spec
    attribute_specs = access_specs + [
        'allocatable',
        'asynchronous',
        'codimension',
        'contiguous',
        'dimension',
        'external',
        'intent',
        'intrinsic',
        'namelist',     # NOTE: Not an attribute...
        # language-binding-spec
        'optional',
        'pointer',
        'protected',
        'save',
        'target',
        'value',
        'volatile',
        'common',       # Deprecated
        'equivalence',  # Deprecated
    ]

    declaration_types = Variable.intrinsic_types + attribute_specs + [
        'type',         # R426, R403
        'enum',         # R459 ("ENUM, BIND(C)")
        'generic',      # R1210
        'interface',    # R1201
        'parameter',    # R551
        'procedure',    # R1213: Procedure declaration statement
        'data',         # R537
        'format',       # R1001
        'entry',        # R1242 (obsolete)
    ]

    unit_prefix = Variable.intrinsic_types + [
        'elemental',
        'impure',
        'non_recursive',
        'pure',
        'recursive',
    ]

    def __init__(self, report=None, verbose=False):
        self.name = None
        self.utype = None
        self.verbose = verbose

        self.subprograms = []
        self.variables = []
        self.blocks = []
        self.namelists = {}
        self.report = report if report else Report()

        self.doc = Document()

    @staticmethod
    def statement(line):
        # TODO: If this ends up being a full type-statement parser, then it
        # needs to be moved into its own class
        idx = next((i for i, w in enumerate(line) if w in Unit.unit_types), -1)

        if idx == 0:
            return True
        elif idx > 0:
            words = iter(line[:idx])

            word = next(words)
            while True:
                try:
                    if word in Variable.intrinsic_types:
                        word = next(words)
                        if word == '(':
                            # TODO: Parse this more formally
                            while word != ')':
                                word = next(words)
                    elif word not in Unit.unit_prefix:
                        return False

                    word = next(words)
                except StopIteration:
                    break
            return True

        else:
            return False

    def end_statement(self, line):
        assert self.utype

        # TODO: Very similar to construct... can I merge somehow?
        if line[0].startswith('end'):
            if len(line) == 1 and line[0] in ('end', 'end' + self.utype):
                return True
            elif len(line) >= 2 and (line[0], line[1]) == ('end', self.utype):
                return True
            else:
                return False

    def parse(self, lines):
        """Parse the lines of a program unit.

        Program units are generally very similar, but we leave it undefined
        here due to some slight differences.
        """
        # NOTE: Unit docstrings precede the header.
        docstrings = lines.docstrings
        self.doc.docstring = '\n'.join(docstrings)
        lines.docstrings = []

        self.doc.header = ' '.join(lines.current_line)

        self.parse_header(lines.current_line)
        self.parse_specification(lines)
        self.parse_execution(lines)
        self.parse_subprogram(lines)

        # Gather any trailing docstrings
        if lines.docstrings:
            self.doc.footer = '\n'.join(lines.docstrings)
            lines.docstrings = []

        # Finalisation
        if self.verbose:
            print('{}: {}'.format(
                  self.utype[0].upper(), ' '.join(lines.current_line)))

    def parse_header(self, line):
        """Parse the name of the program unit, if present.

        Each program unit has a different header format, so this method must be
        overridden by each subclass.
        """
        try:
            self.utype = next(w for w in line if w in Unit.unit_types)
        except StopIteration:
            print(line)
            raise

        # TODO: A safer approach may be to formally parse the first non-unit
        # type as a variable type.  A temporary step is to split the
        # declaration into its (potential) output type and the rest.
        # But for now we just grab the name and ignore the rest.
        # TODO: Could also be that `function` is the only one that is not
        # the first character...
        utype_idx = line.index(self.utype)

        if len(line) >= 2:
            self.name = line[utype_idx + 1]
        else:
            self.name = None

        if self.verbose:
            print('{}: {} '.format(self.utype[0].upper(), ' '.join(line)))

    # Specification

    def parse_specification(self, lines):
        """Parse the specification part (R204) of a program unit (R202).

        Specification parts contain the following:

        1. USE statements (R1109)
        2. IMPORT statements (R1211)
        3. IMPLICIT statements (R205)
        4. Declaration constructs (R207)
        """
        # TODO: `use`, `implicit`, and declarations must appear in that order.
        #       This loop does not check order.
        for line in lines:
            if line[0] == 'use':
                self.parse_use_stmt(line)
            elif line[0] == 'import':
                self.parse_import_stmt(line)
            elif line[0] in 'implicit':
                # TODO: PARAMETER, FORMAT, ENTRY
                self.parse_implicit_stmt(line)
            elif line[0] in Unit.declaration_types:
                self.parse_declaration_construct(lines, line)
            else:
                break

    def parse_use_stmt(self, line):
        """Parse the use statement (R1109) within a specification (R204)."""
        if self.verbose:
            print('U: {}'.format(' '.join(line)))

    def parse_import_stmt(self, line):
        if self.verbose:
            print('i: {}'.format(' '.join(line)))

    def parse_implicit_stmt(self, line):
        if self.verbose:
            print('I: {}'.format(' '.join(line)))

    def parse_declaration_construct(self, lines, line):

        if (line[0] in ('enum', 'interface')
                or (line[0] == 'type' and line[1] != '(')):
            block = Unit(verbose=self.verbose)
            block.parse(lines)

            # TODO: parse name
            block.name = ' '.join(line)
            self.blocks.append(block)

        elif line[0] in Unit.access_specs:
            if self.verbose:
                print('d: {}'.format(' '.join(line)))

        # R357 (placeholder)
        elif line[0] == 'data':
            if self.verbose:
                print('d: {}'.format(' '.join(line)))

        # R551 (placeholder)
        elif line[0] == 'parameter':
            if self.verbose:
                print('p: {}'.format(' '.join(line)))

        else:
            tokens = iter(line)

            tok = next(tokens)
            if tok in Variable.intrinsic_types:
                vtype = tok
            elif tok in ('type', 'class'):
                assert next(tokens) == '('
                vtype = next(tokens)
                assert next(tokens) == ')'
            elif tok == 'namelist':
                self.parse_namelist(line)
                return
            else:
                # Unhandled
                if self.verbose:
                    print('X: {}'.format(' '.join(line)))
                return

            # Character length parsing
            tok = next(tokens)
            if vtype == 'character':
                if tok == '*':
                    tok = next(tokens)

            # Kind (or len) statement
            if tok == '(':
                while tok != ')':
                    tok = next(tokens)
                tok = next(tokens)

            # Attributes
            var_attributes = []
            while tok == ',':
                tok = next(tokens)
                attr = tok
                var_attributes.append(attr)
                if attr in ('dimension', 'intent'):
                    tok = next(tokens)
                    assert tok == '('
                    var_attributes.append(tok)
                    par_count = 1
                    while par_count > 0:
                        tok = next(tokens)
                        if tok == '(':
                            par_count += 1
                        elif tok == ')':
                            par_count -= 1
                        var_attributes.append(tok)
                tok = next(tokens)

            if tok == '::':
                tok = next(tokens)

            vnames = []
            vnames.append(tok)

            for tok in tokens:
                if tok == '(':
                    while tok != ')':
                        tok = next(tokens)
                if tok == ',':
                    try:
                        tok = next(tokens)
                    except StopIteration:
                        self.report.error_endcomma()
                    vnames.append(tok)

            for vname in vnames:
                var = Variable(vname, vtype)

                # TODO: Move all this docstring stuff to a support function
                if lines.docstrings:
                    prior_docs, doc = (
                        lines.docstrings[:-1], lines.docstrings[-1]
                    )
                else:
                    prior_docs = []
                    doc = ''

                if lines.prior_var:
                    lines.prior_var.doc.docstring += '\n'.join(prior_docs)

                var.doc.docstring = doc
                if var_attributes:
                    var.attributes = var_attributes
                lines.docstrings = []
                lines.prior_var = var

                self.variables.append(var)

            if self.verbose:
                print('D: {}'.format(' '.join(line)))

    def parse_namelist(self, line):
        assert(line[0] == 'namelist')
        tokens = iter(line[1:])

        tok = next(tokens)
        while tok:
            assert tok == '/'
            # TODO: Validate group name
            nml_group = next(tokens)
            self.namelists[nml_group] = []
            assert next(tokens) == '/'

            tok = next(tokens)
            while tok and tok != '/':
                # TODO: Validate object name
                self.namelists[nml_group].append(tok)
                tok = next(tokens, None)
                assert tok in (',', '/', None)
                if tok == ',':
                    tok = next(tokens)

        if self.verbose:
            print('N: {}'.format(' '.join(line)))

    # Execution

    def parse_execution(self, lines):
        # First parse the line which terminated specification
        # TODO: How to merge with iteration below?

        line = lines.current_line

        # Exit for interfaces
        if self.utype == 'interface':
            return

        if Construct.statement(line):
            cons = Construct(verbose=self.verbose)
            cons.parse(lines)
        elif self.end_statement(line) or line[0] == 'contains':
            return
        else:
            # Unhandled
            if self.verbose:
                print('E: {}'.format(' '.join(line)))

        # Now iterate over the rest of the lines
        for line in lines:
            # Execution constructs
            if Construct.statement(line):
                cons = Construct(verbose=self.verbose)
                cons.parse(lines)
            elif self.end_statement(line) or line[0] == 'contains':
                # TODO: Use return?
                break
            else:
                # Unhandled
                if self.verbose:
                    print('E: {}'.format(' '.join(line)))

    def parse_subprogram(self, lines):
        # TODO: I think the first line of subprogram is always CONTAINS, so
        # this check may be pointless. (No, not for interfaces)

        line = lines.current_line

        if Unit.statement(line):
            subprog = Unit(verbose=self.verbose)
            subprog.parse(lines)
            self.subprograms.append(subprog)
        elif self.end_statement(line):
            return
        else:
            if self.verbose:
                print('{}: {}'.format(self.utype[0].upper(), ' '.join(line)))

        for line in lines:
            if Unit.statement(line):
                subprog = Unit(verbose=self.verbose)
                subprog.parse(lines)
                self.subprograms.append(subprog)
            elif self.end_statement(line):
                # TODO: Use return?
                break
            else:
                if self.verbose:
                    print('X: {}'.format(' '.join(line)))
