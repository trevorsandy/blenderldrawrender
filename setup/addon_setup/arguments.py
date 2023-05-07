import sys
import argparse

class BlenderArgumentParser(argparse.ArgumentParser):
    """Process command line arguments after '--'"""

    def _argv_after_doubledash(self):
        try:
            arg_index = sys.argv.index("--")
            return sys.argv[arg_index+1:]  # arguments after '--'
        except ValueError as e:
            return []

    def parse_args(self):                  # overrides superclass
        return super().parse_args(args=self._argv_after_doubledash())

if __name__ == "__main__":
    print("Process command line arguments after '--'", end=f"\n{'-' * 41}\n")