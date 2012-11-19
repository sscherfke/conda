''' The package_spec module contains the package_spec class, and utility functions for manipulating sets of package specifications.

'''


from distutils.version import LooseVersion
from itertools import combinations, groupby, izip, tee

from naming import split_spec_string
from verlib import NormalizedVersion, suggest_normalized_version


class package_spec(object):
    '''
    Encapsulates a package name and an optional version (or partial version) along with an optional build string for
    use as a package specification.

    Parameters
    ----------
    spec_string : str
        a string containing a package name and (optional) version and (optional) build string, separated by a spaces or by '='


    Attributes
    ----------
    build : str
    name : str
    version : LooseVersion

    Examples
    --------
    >>> spec = package_spec("python 2.7")
    >>> spec.name
    'python'
    >>> spec.version
    LooseVersion('2.7')

    '''

    __slots__ = ['__name', '__version', '__build']

    def __init__(self, spec_string):
        components = split_spec_string(spec_string)

        self.__name = components[0]

        self.__version = None
        if len(components) > 1:
            self.__version = LooseVersion(components[1])

        self.__build = None
        if len(components) == 3:
            self.__build = components[2]

    @property
    def name(self):
        ''' package name

        '''
        return self.__name

    @property
    def version(self):
        ''' package version or partial version

        '''
        return self.__version

    @property
    def build(self):
        ''' package build string (or None)

        '''
        return self.__build

    def __str__(self):
        if self.build:
            return '%s=%s=%s' % (self.name, self.version.vstring, self.build)
        elif self.version:
            return '%s=%s' % (self.name, self.version.vstring)
        else:
            return '%s' % self.name

    def __repr__(self):
        if self.build:
            return "package_spec('%s %s %s')" % (self.name, self.version.vstring, self.build)
        elif self.version:
            return "package_spec('%s %s')" % (self.name, self.version.vstring)
        else:
            return "package_spec('%s')" % self.name

    def __hash__(self):
        if self.version:
            return hash((self.name, self.version.vstring, self.build))
        else:
            return hash((self.name, self.version, self.build))

    def __cmp__(self, other):
        # NormalizedVersion seems to not work perfectly if 'rc' is adjacent to the last version digit
        sv = self.version.vstring.replace('rc', '.rc') if self.version else None
        ov = other.version.vstring.replace('rc', '.rc') if other.version else None
        try:
            return cmp(
                (self.name, NormalizedVersion(suggest_normalized_version(sv)), self.build),
                (other.name, NormalizedVersion(suggest_normalized_version(ov)), other.build)
            )
        except:
            return cmp(
                (self.name, sv, self.build),
                (other.name, ov, other.build)
            )


def find_inconsistent_specs(specs):
    ''' Iterates over a set of package specifications, finding those that share a name
    but have inconsistent versions

    Parameters
    ----------
    specs : iterable collection of :py:class:`package_spec <conda.package_spec.package_spec>` objects
        package specifications to check for inconsistencies

    Returns
    -------
    inconsistent_specs : set of :py:class:`package_spec <conda.package_spec.package_spec>` objects
        all inconsistent package specifications present in `specs`

    Examples
    --------
    >>> r,s,t = package_spec('python 2.7'), package_spec('python 3.1'), package_spec('numpy 1.2.3')
    >>> specs = [r,s,t]
    >>> find_inconsistent_specs(specs)
    set([package_spec('python 3.1'), package_spec('python 2.7')])

    '''

    inconsistent = dict()

    grouped = group_package_specs_by_name(specs)

    for name, specs in grouped.items():
        if len(specs) < 2: continue
        for s1, s2 in combinations(specs, 2):

            if not s1.version or not s2.version: continue

            v1, v2 = tuple(s1.version.version), tuple(s2.version.version)
            vlen = min(len(v1), len(v2))
            if v1[:vlen] != v2[:vlen]:
                inconsistent[name] = specs
                break

    return inconsistent


def apply_default_spec(specs, default_spec):
    '''
    Examines a collection of package specifications and adds default_spec to it, if no
    other package specification for the same package specified by default_spec is already present.

    Parameters
    ----------
    specs : iterable of :py:class:`package_spec <conda.package_spec.package_spec>` objects
        package specifications to apply defaults to
    default_spec : :py:class:`package_spec <conda.package_spec.package_spec>` object
        default package specification to apply to `specs`

    Returns
    -------
    updated_specs : set of :py:class:`package_spec <conda.package_spec.package_spec>` objects
        `specs` with `default_spec` applied, if necessary

    '''
    specs = set(specs)
    grouped = group_package_specs_by_name(specs)
    if default_spec.name not in grouped.keys():
        specs.add(default_spec)
    return specs


def sort_package_specs_by_name(specs, reverse=False):
    ''' sort a collection of package specifications by their :ref:`package names <package_name>`

    Parameters
    ----------
    specs : iterable of :py:class:`package_spec <conda.package_spec.package_spec>`
        package specifications to sort by package name
    reverse : bool, optional
        whether to sort in reverse order

    Returns
    -------
    sorted : list of :py:class:`package_spec <conda.package_spec.package_spec>`
        package specifications sorted by package name

    '''
    return sorted(
        list(specs),
        reverse=reverse,
        key=lambda spec: spec.name
    )


def group_package_specs_by_name(specs):
    ''' group a collection of package specifications by their :ref:`package names <package_name>`

    Parameters
    ----------
    specs : iterable of :py:class:`package_spec <conda.package_spec.package_spec>`
        package specifications to group by package name

    Returns
    -------
    grouped : dict of (str, set of :py:class:`package_spec <conda.package_spec.package_spec>`)
        dictionary of sets of package specifications, indexed by package name

    '''
    return dict((k, set(list(g))) for k, g in groupby(sort_package_specs_by_name(specs), key=lambda spec: spec.name))

