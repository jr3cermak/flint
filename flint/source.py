import os
import sys

from flint.fortlines import FortLines
from flint.report import Report
from flint.unit import Unit
from flint.tokenizer import Tokenizer


class Source(object):
    def __init__(self, project=None):
        self.project = project

        # Filepath
        self.path = None
        self.abspath = None

        # Program units
        self.units = []

        # Diagnostics
        self.linewidths = []
        self.whitespace = []

        self.report = Report()

    def parse(self, path):
        # Resolve filepaths
        if os.path.isabs(path):
            self.abspath = path

            if self.project:
                root_path = self.project.path
                plen = len(root_path)
                assert path[:plen] == self.project.path
                self.abspath = path[plen:]
            else:
                self.path = self.abspath

        else:
            self.path = path
            if self.project:
                # TODO: Probably need a root path consistency check here...
                self.abspath = os.path.join(self.project.path, path)
            else:
                self.abspath = os.path.abspath(path)

        tokenizer = Tokenizer()
        line_cnt = 0
        raw_lines = []
        print('{} ({})'.format(self.path, self.abspath))

        # TODO: pycodestyle has a better way to deal with nonunicode files
        with open(self.path, errors='replace') as srcfile:
            for line in srcfile:
                line_cnt += 1

                self.report.check_linewidth(line, line_cnt)

                try:
                    tokens = tokenizer.parse(line)
                except ValueError:
                    print('error', srcfile)
                    print(line)
                    sys.exit()

                if tokens:
                    self.report.check_trailing_whitespace(tokens, line_cnt)

                raw_lines.append(tokens)

        # Line cleanup
        # NOTE: Pre-calculating all these stats is a bit memory-intensive for
        #       projects approaching ~100k to 1M lines.
        # TODO: Make this a function, move inside flines loop
        #       (May also require a more sophisticated FortLines)
        # TODO: Or maybe create an iterator that optionally skips whitespace
        src_lines = []
        for line in raw_lines:

            # Record line widths
            width = len(''.join(line))
            self.linewidths.append(width)

            # Strip comments and preprocessed lines
            # TODO: Handle preprocessed lines better
            line = [w for w in line if w[0] not in '!#']

            # Track whitespace between tokens
            # TODO: Move first whitespace to `self.indent`?
            line_ws = []
            for word in line:
                if all(c == ' ' for c in word):
                    line_ws.append(len(word))
                else:
                    line_ws.append(0)

            self.whitespace.append(line_ws)

            # TODO: Check token case consistency
            #       For now just convert to lowercase
            line = [tok.lower() if tok[0] not in '\'"' else tok
                    for tok in line]

            # Remove whitespace
            tokenized_line = [tok for tok in line
                              if not all(c == ' ' for c in tok)]
            if tokenized_line:
                src_lines.append(tokenized_line)

        flines = FortLines(src_lines)

        for line in flines:
            if Unit.statement(line):
                unit = Unit()
                unit.parse(flines)
                self.units.append(unit)
            else:
                # Unresolved line
                print('X: {}'.format(' '.join(line)))
