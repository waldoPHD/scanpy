import inspect
import sys
from enum import IntEnum
from pathlib import Path
from time import time
from typing import Tuple, Union, Any, List, Iterable, TextIO, Optional

from . import logging
from .logging import _set_log_level, _set_log_file, RootLogger

_VERBOSITY_TO_LOGLEVEL = {
    'error': 'ERROR',
    'warning': 'WARNING',
    'info': 'INFO',
    'hint': 'HINT',
    'debug': 'DEBUG',
}
verbosity_names = list(_VERBOSITY_TO_LOGLEVEL.keys())
# Python 3.7 ensures iteration order
for v, level in enumerate(list(_VERBOSITY_TO_LOGLEVEL.values())):
    _VERBOSITY_TO_LOGLEVEL[v] = level


class Verbosity(IntEnum):
    error = 0
    warn = 1
    info = 2
    hint = 3
    debug = 4


def _type_check(var: Any, varname: str, types: Union[type, Tuple[type, ...]]):
    if isinstance(var, types):
        return
    if isinstance(types, type):
        possible_types_str = types.__name__
    else:
        type_names = [t.__name__ for t in types]
        possible_types_str = "{} or {}".format(
            ", ".join(type_names[:-1]), type_names[-1]
        )
    raise TypeError(f"{varname} must be of type {possible_types_str}")


class ScanpyConfig:
    """Config manager for scanpy.
    """

    def __init__(
        self,
        *,
        verbosity: str = "warning",
        plot_suffix: str = "",
        file_format_data: str = "h5ad",
        file_format_figs: str = "pdf",
        autosave: bool = False,
        autoshow: bool = True,
        writedir: Union[str, Path] = "./write/",
        cachedir: Union[str, Path] = "./cache/",
        datasetdir: Union[str, Path] = "./data/",
        figdir: Union[str, Path] = "./figures/",
        max_memory=15,
        n_jobs=1,
        logfile: Union[str, Path, None] = None,
        categories_to_ignore: Iterable[str] = ("N/A", "dontknow", "no_gate", "?"),
        _frameon: bool = True,
        _vector_friendly: bool = False,
        _low_resolution_warning: bool = True
    ):
        # logging
        self._root_logger = RootLogger(logging.INFO)  # level will be replaced
        self.logfile = logfile
        self.verbosity = verbosity
        # rest
        self.plot_suffix = plot_suffix
        self.file_format_data = file_format_data
        self.file_format_figs = file_format_figs
        self.autosave = autosave
        self.autoshow = autoshow
        self.writedir = writedir
        self.cachedir = cachedir
        self.datasetdir = datasetdir
        self.figdir = figdir
        self.max_memory = max_memory
        self.n_jobs = n_jobs
        self.categories_to_ignore = categories_to_ignore
        self._frameon = _frameon
        """bool: See set_figure_params."""

        self._vector_friendly = _vector_friendly
        """Set to true if you want to include pngs in svgs and pdfs.
        """

        self._low_resolution_warning = _low_resolution_warning
        """Print warning when saving a figure with low resolution."""

        self._start = time()
        """Time when the settings module is first imported."""

        self._previous_time = self._start
        """Variable for timing program parts."""

        self._previous_memory_usage = -1
        """Stores the previous memory usage."""

    @property
    def verbosity(self) -> Verbosity:
        """
        Set global verbosity level.

        Level 0: only show 'error' messages.
        Level 1: also show 'warning' messages.
        Level 2: also show 'info' messages.
        Level 3: also show 'hint' messages.
        Level 4: also show very detailed progress for 'debug'ging.
        """
        return self._verbosity

    @verbosity.setter
    def verbosity(self, verbosity: Union[Verbosity, int, str]):
        verbosity_str_options = [
            v for v in _VERBOSITY_TO_LOGLEVEL
            if isinstance(v, str)
        ]
        if isinstance(verbosity, Verbosity):
            self._verbosity = verbosity
        elif isinstance(verbosity, int):
            self._verbosity = Verbosity(verbosity)
        elif isinstance(verbosity, str):
            verbosity = verbosity.lower()
            if verbosity not in verbosity_str_options:
                raise ValueError(
                    f"Cannot set verbosity to {verbosity}. "
                    f"Accepted string values are: {verbosity_str_options}"
                )
            else:
                self._verbosity = Verbosity(verbosity_str_options.index(verbosity))
        else:
            _type_check(verbosity, "verbosity", (str, int))
        _set_log_level(self, _VERBOSITY_TO_LOGLEVEL[self._verbosity])

    @property
    def plot_suffix(self) -> str:
        """Global suffix that is appended to figure filenames.
        """
        return self._plot_suffix

    @plot_suffix.setter
    def plot_suffix(self, plot_suffix: str):
        _type_check(plot_suffix, "plot_suffix", str)
        self._plot_suffix = plot_suffix

    @property
    def file_format_data(self) -> str:
        """File format for saving AnnData objects.

        Allowed are 'txt', 'csv' (comma separated value file) for exporting and 'h5ad'
        (hdf5) for lossless saving.
        """
        return self._file_format_data

    @file_format_data.setter
    def file_format_data(self, file_format: str):
        _type_check(file_format, "file_format_data", str)
        file_format_options = {"txt", "csv", "h5ad"}
        if file_format not in file_format_options:
            raise ValueError(
                f"Cannot set file_format_data to {file_format}. "
                f"Must be one of {file_format_options}"
            )
        self._file_format_data = file_format

    @property
    def file_format_figs(self) -> str:
        """File format for saving figures.

        For example 'png', 'pdf' or 'svg'. Many other formats work as well (see
        `matplotlib.pyplot.savefig`).
        """
        return self._file_format_figs

    @file_format_figs.setter
    def file_format_figs(self, figure_format: str):
        _type_check(figure_format, "figure_format_data", str)
        self._file_format_figs = figure_format

    @property
    def autosave(self) -> bool:
        """bool: Save plots/figures as files in directory 'figs'.

        Do not show plots/figures interactively.
        """
        return self._autosave

    @autosave.setter
    def autosave(self, autosave: bool):
        _type_check(autosave, "autosave", bool)
        self._autosave = autosave

    @property
    def autoshow(self) -> bool:
        """bool: Show all plots/figures automatically if autosave == False.

        There is no need to call the matplotlib pl.show() in this case.
        """
        return self._autoshow

    @autoshow.setter
    def autoshow(self, autoshow: bool):
        _type_check(autoshow, "autoshow", bool)
        self._autoshow = autoshow

    @property
    def writedir(self) -> Path:
        """Directory where the function scanpy.write writes to by default.
        """
        return self._writedir

    @writedir.setter
    def writedir(self, writedir: Union[str, Path]):
        _type_check(writedir, "writedir", (str, Path))
        self._writedir = Path(writedir)

    @property
    def cachedir(self) -> Path:
        """Default cache directory.
        """
        return self._cachedir

    @cachedir.setter
    def cachedir(self, cachedir: Union[str, Path]):
        _type_check(cachedir, "cachedir", (str, Path))
        self._cachedir = Path(cachedir)

    @property
    def datasetdir(self) -> Path:
        """Default directory for ``sc.datasets`` to download data to.
        """
        return self._datasetdir

    @datasetdir.setter
    def datasetdir(self, datasetdir: Union[str, Path]):
        _type_check(datasetdir, "datasetdir", (str, Path))
        self._datasetdir = Path(datasetdir).resolve()

    @property
    def figdir(self) -> Path:
        """Directory where plots are saved.
        """
        return self._figdir

    @figdir.setter
    def figdir(self, figdir: Union[str, Path]):
        _type_check(figdir, "figdir", (str, Path))
        self._figdir = Path(figdir)

    @property
    def max_memory(self) -> Union[int, float]:
        """Maximal memory usage in Gigabyte.

        Is currently not well respected....
        """
        return self._max_memory

    @max_memory.setter
    def max_memory(self, max_memory: Union[int, float]):
        _type_check(max_memory, "max_memory", (int, float))
        self._max_memory = max_memory

    @property
    def n_jobs(self) -> int:
        """Default number of jobs/ CPUs to use for parallel computing.
        """
        return self._n_jobs

    @n_jobs.setter
    def n_jobs(self, n_jobs: int):
        _type_check(n_jobs, "n_jobs", int)
        self._n_jobs = n_jobs

    @property
    def logpath(self) -> Optional[Path]:
        """The file path `logfile` was set to."""
        return self._logpath

    @logpath.setter
    def logpath(self, logpath: Union[str, Path, None]):
        _type_check(logpath, "logfile", (str, Path))
        # set via “file object” branch of logfile.setter
        self.logfile = Path(logpath).open('a')
        self._logpath = Path(logpath)

    @property
    def logfile(self) -> TextIO:
        """The open file to write logs to.

        Set it to a :class:`~pathlib.Path` or :class:`str: to open a new one.
        The default `None` corresponds to :obj:`sys.stdout` in jupyter notebooks
        and to :obj:`sys.stderr` otherwise.

        For backwards compatibility, setting it to `''` behaves like setting it to `None`.
        """
        return self._logfile

    @logfile.setter
    def logfile(self, logfile: Union[str, Path, TextIO, None]):
        if not hasattr(logfile, 'write') and logfile:
            self.logpath = logfile
        else:  # file object
            if not logfile:  # None or ''
                logfile = sys.stdout if self._is_run_from_ipython() else sys.stderr
            self._logfile = logfile
            self._logpath = None
            _set_log_file(self)

    @property
    def categories_to_ignore(self) -> List[str]:
        """Categories that are omitted in plotting etc.
        """
        return self._categories_to_ignore

    @categories_to_ignore.setter
    def categories_to_ignore(self, categories_to_ignore: Iterable[str]):
        categories_to_ignore = list(categories_to_ignore)
        for i, cat in enumerate(categories_to_ignore):
            _type_check(cat, f"categories_to_ignore[{i}]", str)
        self._categories_to_ignore = categories_to_ignore

    # --------------------------------------------------------------------------------
    # Functions
    # --------------------------------------------------------------------------------

    def set_figure_params(
        self,
        scanpy=True,
        dpi=80,
        dpi_save=150,
        frameon=True,
        vector_friendly=True,
        fontsize=14,
        color_map=None,
        format="pdf",
        transparent=False,
        ipython_format="png2x",
    ):
        """Set resolution/size, styling and format of figures.

        Parameters
        ----------
        scanpy : `bool`, optional (default: `True`)
            Init default values for ``matplotlib.rcParams`` suited for Scanpy.
        dpi : `int`, optional (default: `80`)
            Resolution of rendered figures - this influences the size of figures in notebooks.
        dpi_save : `int`, optional (default: `150`)
            Resolution of saved figures. This should typically be higher to achieve
            publication quality.
        frameon : `bool`, optional (default: `True`)
            Add frames and axes labels to scatter plots.
        vector_friendly : `bool`, optional (default: `True`)
            Plot scatter plots using `png` backend even when exporting as `pdf` or `svg`.
        fontsize : `int`, optional (default: 14)
            Set the fontsize for several `rcParams` entries. Ignored if `scanpy=False`.
        color_map : `str`, optional (default: `None`)
            Convenience method for setting the default color map. Ignored if `scanpy=False`.
        format : {'png', 'pdf', 'svg', etc.}, optional (default: 'pdf')
            This sets the default format for saving figures: `file_format_figs`.
        transparent : `bool`, optional (default: `True`)
            Save figures with transparent back ground. Sets
            `rcParams['savefig.transparent']`.
        ipython_format : list of `str`, optional (default: 'png2x')
            Only concerns the notebook/IPython environment; see
            `IPython.core.display.set_matplotlib_formats` for more details.
        """
        try:
            import IPython
            IPython.core.display.set_matplotlib_formats(ipython_format)
        except Exception:
            pass
        from matplotlib import rcParams
        self._vector_friendly = vector_friendly
        self.file_format_figs = format
        if dpi is not None:
            rcParams["figure.dpi"] = dpi
        if dpi_save is not None:
            rcParams["savefig.dpi"] = dpi_save
        if transparent is not None:
            rcParams["savefig.transparent"] = transparent
        if scanpy:
            from .plotting._rcmod import set_rcParams_scanpy
            set_rcParams_scanpy(fontsize=fontsize, color_map=color_map)
        self._frameon = frameon

    @staticmethod
    def _is_run_from_ipython():
        """Determines whether run from Ipython.

        Only affects progress bars.
        """
        try:
            __IPYTHON__
            return True
        except NameError:
            return False

    def __str__(self) -> str:
        return '\n'.join(
            f'{k} = {v!r}'
            for k, v in inspect.getmembers(self)
            if not k.startswith("_") and not k == 'getdoc'
        )


settings = ScanpyConfig()
