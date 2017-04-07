from flint.units.unit import Unit


class Subroutine(Unit):

    def __init__(self):
        self.name = None

        self.modules = []
        self.functions = []
        self.variables = []

    def parse_name(self, line):
        assert(len(line) <= 2)
        assert(line[0] == 'subroutine')

        if len(line) == 2:
            name = line[1]
        else:
            name = None

        self.name = name

    def parse(self, lines):
        """Parse the lines of a program unit.

        Each program unit consists of three sections:

        1. Specification part (R204)
        2. Execution part (R209)
        3. Subprograms:
           a. Internal subprogram part (R211)
           b. Module subprogram part (R1107)

        None of this has yet been implemented.  Below is just some basic
        handling of DO and IF constructs.
        """
        self.parse_name(lines.current_line)
        self.parse_specification(lines)
        self.parse_execution(lines)
        self.parse_subprogram(lines)
