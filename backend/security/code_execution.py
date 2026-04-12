import math
import statistics
import itertools
import functools
import collections
import json
import re
import datetime

import pandas
import numpy
import scipy
import polars

# import resource # doesnt work for windows
import signal


class SaveExecution:

    def __init__(self, MAX_MEMORY_MB: int = 500, MAX_EXECUTION_SECONDS: int = 3):
        self.MAX_MEMORY_MB = MAX_MEMORY_MB
        self.MAX_EXECUTION_SECONDS = MAX_EXECUTION_SECONDS
        self._orig = {}

    # def limit_resources(self): # doesnt work for windows
    #     resource.setrlimit(resource.RLIMIT_AS, (self.MAX_MEMORY_MB * 1024 * 1024,
    #                                             self.MAX_EXECUTION_SECONDS * 1024 * 1024))

        # def timeout_handler(signum, frame):
        #     raise TimeoutError("Execution time exceeded")
        #
        # signal.signal(signal.SIGXCPU, timeout_handler)
        # resource.setrlimit(resource.RLIMIT_CPU, (self.MAX_EXECUTION_SECONDS, self.MAX_MEMORY_MB))
    def _save_originals(self):
        import pandas, numpy, polars

        if self._orig:
            return

        self._orig = {
            # pandas
            "pandas.read_csv": pandas.read_csv,
            "pandas.read_parquet": pandas.read_parquet,
            "pandas.read_excel": pandas.read_excel,
            "pandas.DataFrame.to_csv": pandas.DataFrame.to_csv,
            "pandas.DataFrame.to_parquet": pandas.DataFrame.to_parquet,

            # numpy
            "numpy.load": numpy.load,
            "numpy.save": numpy.save,
            "numpy.savez": numpy.savez,

            # polars
            "polars.read_csv": polars.read_csv,
            "polars.scan_csv": polars.scan_csv,
            "polars.read_parquet": polars.read_parquet,
            "polars.scan_parquet": polars.scan_parquet,
            "polars.DataFrame.write_csv": polars.DataFrame.write_csv,
            "polars.DataFrame.write_parquet": polars.DataFrame.write_parquet,
        }

    def disable_file_io(self):

        self._save_originals()

        # pandas
        pandas.read_csv = None
        pandas.read_parquet = None
        pandas.read_excel = None
        pandas.DataFrame.to_csv = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("File pandas writing disabled"))
        pandas.DataFrame.to_parquet = pandas.DataFrame.to_csv

        # numpy
        numpy.load = None
        numpy.save = None
        numpy.savez = None

        # polars
        polars.read_csv = None
        polars.scan_csv = None
        polars.read_parquet = None
        polars.scan_parquet = None
        polars.DataFrame.write_csv = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("File polars writing disabled"))
        polars.DataFrame.write_parquet = polars.DataFrame.write_csv


    def build_sandbox_globals(self, extra_globals):
        self.disable_file_io()

        sandbox_globals = {
            # "__builtins__": {},
            "math": math,
            "statistics": statistics,
            "itertools": itertools,
            "functools": functools,
            "collections": collections,
            "json": json,
            "re": re,
            "datetime": datetime,
            "pandas": pandas,
            "numpy": numpy,
            "scipy": scipy,
            "polars": polars,
        }

        if extra_globals:
            sandbox_globals.update(extra_globals)

        return sandbox_globals

    def restore_originals(self):
        import pandas, numpy, polars

        # pandas
        pandas.read_csv = self._orig["pandas.read_csv"]
        pandas.read_parquet = self._orig["pandas.read_parquet"]
        pandas.read_excel = self._orig["pandas.read_excel"]
        pandas.DataFrame.to_csv = self._orig["pandas.DataFrame.to_csv"]
        pandas.DataFrame.to_parquet = self._orig["pandas.DataFrame.to_parquet"]

        # numpy
        numpy.load = self._orig["numpy.load"]
        numpy.save = self._orig["numpy.save"]
        numpy.savez = self._orig["numpy.savez"]

        # polars
        polars.read_csv = self._orig["polars.read_csv"]
        polars.scan_csv = self._orig["polars.scan_csv"]
        polars.read_parquet = self._orig["polars.read_parquet"]
        polars.scan_parquet = self._orig["polars.scan_parquet"]
        polars.DataFrame.write_csv = self._orig["polars.DataFrame.write_csv"]
        polars.DataFrame.write_parquet = self._orig["polars.DataFrame.write_parquet"]
