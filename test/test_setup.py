"""Tests for setup scripts."""

import importlib
import itertools
import os
import pathlib
import runpy
import subprocess
import sys
import tempfile
import typing as t
import unittest

__updated__ = '2017-10-12'


def run_program(*args, glob: bool = False):
    """Run subprocess with given args. Use path globbing for each arg that contains an asterisk."""
    if glob:
        cwd = pathlib.Path.cwd()
        args = tuple(itertools.chain.from_iterable(
            list(str(_.relative_to(cwd)) for _ in cwd.glob(arg)) if '*' in arg else [arg]
            for arg in args))
    process = subprocess.Popen(args)
    process.wait()
    if process.returncode != 0:
        raise AssertionError('execution of {} returned {}'.format(args, process.returncode))
    return process


def run_pip(*args, **kwargs):
    python_exec_name = pathlib.Path(sys.executable).name
    pip_exec_name = python_exec_name.replace('python', 'pip')
    run_program(pip_exec_name, *args, **kwargs)


def run_module(name: str, *args, run_name: str = '__main__'):
    """Execute module with given name after rewriting sys.argv to given values."""
    backup_sys_argv = sys.argv
    sys.argv = [name.replace('.', os.sep) + '.py'] + list(args)
    runpy.run_module(name, run_name=run_name)
    sys.argv = backup_sys_argv


def import_module(name: str = 'setup') -> 'module':
    setup_module = importlib.import_module(name)
    return setup_module


def import_module_member(module_name: str, member_name: str) -> t.Any:
    module = import_module(module_name)
    return getattr(module, member_name)


#def import_module_members(module_name: str, member_names: t.Iterable[str]) -> t.List[t.Any]:
#    module = import_module(module_name)
#    return [getattr(module, member_name) for member_name in member_names]


CLASSIFIERS_LICENSES = (
    'License :: OSI Approved :: Python License (CNRI Python License)',
    'License :: OSI Approved :: Python Software Foundation License',
    'License :: Other/Proprietary License',
    'License :: Public Domain')

CLASSIFIERS_PYTHON_VERSIONS = tuple("""Programming Language :: Python
Programming Language :: Python :: 2
Programming Language :: Python :: 2.3
Programming Language :: Python :: 2.4
Programming Language :: Python :: 2.5
Programming Language :: Python :: 2.6
Programming Language :: Python :: 2.7
Programming Language :: Python :: 2 :: Only
Programming Language :: Python :: 3
Programming Language :: Python :: 3.0
Programming Language :: Python :: 3.1
Programming Language :: Python :: 3.2
Programming Language :: Python :: 3.3
Programming Language :: Python :: 3.4
Programming Language :: Python :: 3.5
Programming Language :: Python :: 3.6
Programming Language :: Python :: 3.7
Programming Language :: Python :: 3 :: Only""".splitlines())

CLASSIFIERS_PYTHON_IMPLEMENTATIONS = tuple("""Programming Language :: Python :: Implementation
Programming Language :: Python :: Implementation :: CPython
Programming Language :: Python :: Implementation :: IronPython
Programming Language :: Python :: Implementation :: Jython
Programming Language :: Python :: Implementation :: MicroPython
Programming Language :: Python :: Implementation :: PyPy
Programming Language :: Python :: Implementation :: Stackless""".splitlines())

CLASSIFIERS_VARIOUS = (
    'Framework :: IPython',
    'Topic :: Scientific/Engineering',
    'Topic :: Sociology',
    'Topic :: Security :: Cryptography',
    'Topic :: Software Development :: Libraries :: Python Modules',
    'Topic :: Software Development :: Version Control :: Git',
    'Topic :: System',
    'Topic :: Utilities')

CLASSIFIERS_LICENSES_TUPLES = tuple((_,) for _ in CLASSIFIERS_LICENSES) + ((),)

CLASSIFIERS_PYTHON_VERSIONS_COMBINATIONS = tuple((_,) for _ in CLASSIFIERS_PYTHON_VERSIONS)

CLASSIFIERS_PYTHON_IMPLEMENTATIONS_TUPLES = tuple((_,) for _ in CLASSIFIERS_PYTHON_IMPLEMENTATIONS)

#CLASSIFIERS_VARIOUS_PERMUTATIONS = tuple(itertools.chain.from_iterable(
#    itertools.permutations(..., n)
#    for n in range(...)
#    ))

CLASSIFIERS_VARIOUS_COMBINATIONS = tuple(itertools.combinations(
    CLASSIFIERS_VARIOUS, len(CLASSIFIERS_VARIOUS) - 1)) + (CLASSIFIERS_VARIOUS,)

ALL_CLASSIFIERS_VARIANTS = [
    licenses + versions + implementations + various
    for licenses in CLASSIFIERS_LICENSES_TUPLES
    for versions in CLASSIFIERS_PYTHON_VERSIONS_COMBINATIONS
    for implementations in CLASSIFIERS_PYTHON_IMPLEMENTATIONS_TUPLES
    for various in CLASSIFIERS_VARIOUS_COMBINATIONS]


def get_package_folder_name():
    """Attempt to guess the built package name."""
    cwd = pathlib.Path.cwd()
    directories = [
        path for path in cwd.iterdir() if pathlib.Path(cwd, path).is_dir() \
            and pathlib.Path(cwd, path, '__init__.py').is_file() \
            and path.name != 'test']
    assert len(directories) == 1, directories
    return directories[0].name


class UnitTests(unittest.TestCase):
    """Test basic functionalities of the setup boilerplate."""

    def test_find_version(self):
        find_version = import_module_member('setup_boilerplate', 'find_version')
        result = find_version(get_package_folder_name())
        self.assertIsInstance(result, str)

    def test_find_packages(self):
        find_packages = import_module_member('setup_boilerplate', 'find_packages')
        results = find_packages()
        self.assertIsInstance(results, list)
        for result in results:
            self.assertIsInstance(result, str)

    def test_parse_readme(self):
        parse_readme = import_module_member('setup_boilerplate', 'parse_readme')
        result = parse_readme()
        self.assertIsInstance(result, str)

    def test_parse_reqs(self):
        parse_requirements = import_module_member('setup_boilerplate', 'parse_requirements')
        results = parse_requirements()
        self.assertIsInstance(results, list)
        self.assertTrue(all(isinstance(result, str) for result in results), msg=results)

    def test_parse_reqs_empty(self):
        parse_requirements = import_module_member('setup_boilerplate', 'parse_requirements')
        reqs_file = tempfile.NamedTemporaryFile('w', delete=False)
        reqs_file.close()
        results = parse_requirements(reqs_file.name)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)
        os.remove(reqs_file.name)

    def test_parse_reqs_comments(self):
        parse_requirements = import_module_member('setup_boilerplate', 'parse_requirements')
        reqs = ['# comment', 'numpy', '', '# another comment', 'scipy', '', '# one more comment']
        reqs_file = tempfile.NamedTemporaryFile('w', delete=False)
        for req in reqs:
            print(req, file=reqs_file)
        reqs_file.close()
        results = parse_requirements(reqs_file.name)
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertLess(len(results), len(reqs))
        os.remove(reqs_file.name)

    def test_find_req_py_ver(self):
        find_required_python_version = import_module_member(
            'setup_boilerplate', 'find_required_python_version')
        for variant in ALL_CLASSIFIERS_VARIANTS:
            with self.subTest(variant=variant):
                result = find_required_python_version(variant)
                if result is not None:
                    self.assertIsInstance(result, str)

    def test_find_req_py_ver_reversed(self):
        find_required_python_version = import_module_member(
            'setup_boilerplate', 'find_required_python_version')
        classifiers = [
            'Programming Language :: Python :: 3.4',
            'Programming Language :: Python :: 3.5',
            'Programming Language :: Python :: 3.6']
        req = find_required_python_version(classifiers)
        self.assertEqual(req, '>=3.4')
        req = find_required_python_version(reversed(classifiers))
        self.assertEqual(req, '>=3.4')

    def test_find_req_py_ver_none(self):
        find_required_python_version = import_module_member(
            'setup_boilerplate', 'find_required_python_version')
        result = find_required_python_version([])
        self.assertIsNone(result)

    def test_find_req_py_ver_many_only(self):
        find_required_python_version = import_module_member(
            'setup_boilerplate', 'find_required_python_version')
        classifiers = [
            'Programming Language :: Python :: 2 :: Only',
            'Programming Language :: Python :: 3 :: Only']
        with self.assertRaises(ValueError):
            find_required_python_version(classifiers)

    def test_find_req_py_ver_conflict(self):
        find_required_python_version = import_module_member(
            'setup_boilerplate', 'find_required_python_version')
        classifier_variants = [
            ['Programming Language :: Python :: 2.7',
             'Programming Language :: Python :: 3 :: Only'],
            ['Programming Language :: Python :: 2 :: Only',
             'Programming Language :: Python :: 3.0']]
        for classifiers in classifier_variants:
            with self.assertRaises(ValueError):
                find_required_python_version(classifiers)

    def test_package(self):
        package = import_module_member('setup_boilerplate', 'Package')
        class Package(package): # pylint: disable=too-few-public-methods
            name = 'package name'
            description = 'package description'
        self.assertIsNone(Package.try_fields())
        self.assertEqual(Package.try_fields('name', 'description'), 'package name')
        self.assertEqual(Package.try_fields('bad_field', 'description'), 'package description')


class IntergrationTests(unittest.TestCase):
    """Test if the boilerplate can actually create a valid package."""

    pkg_name = get_package_folder_name()

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_build_binary(self):
        run_module('setup', 'bdist')
        self.assertTrue(os.path.isdir('dist'))

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_build_wheel(self):
        run_module('setup', 'bdist_wheel')
        self.assertTrue(os.path.isdir('dist'))

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_build_source(self):
        run_module('setup', 'sdist', '--formats=gztar,zip')
        self.assertTrue(os.path.isdir('dist'))

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_clean(self):
        run_module('setup', 'bdist')
        self.assertTrue(os.path.isdir('build'))
        package = import_module_member('setup_boilerplate', 'Package')
        package.clean()
        os.mkdir('build')
        package.clean()
        package.clean()
        self.assertFalse(os.path.isdir('build'))

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_install_code(self):
        run_pip('install', '.')
        run_pip('uninstall', '-y', self.pkg_name)

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_install_source_tar(self):
        find_version = import_module_member('setup_boilerplate', 'find_version')
        version = find_version(self.pkg_name)
        run_pip('install', 'dist/*-{}.tar.gz'.format(version), glob=True)
        run_pip('uninstall', '-y', self.pkg_name)

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_install_source_zip(self):
        find_version = import_module_member('setup_boilerplate', 'find_version')
        version = find_version(self.pkg_name)
        run_pip('install', 'dist/*-{}.zip'.format(version), glob=True)
        run_pip('uninstall', '-y', self.pkg_name)

    @unittest.skipUnless(os.environ.get('TEST_PACKAGING'), 'skipping packaging test')
    def test_install_wheel(self):
        find_version = import_module_member('setup_boilerplate', 'find_version')
        version = find_version(self.pkg_name)
        run_pip('install', 'dist/*-{}-*.whl'.format(version), glob=True)
        run_pip('uninstall', '-y', self.pkg_name)

    def test_pip_error(self):
        with self.assertRaises(AssertionError):
            run_pip('wrong_pip_command')

    def test_setup_do_nothing_or_error(self):
        run_module('setup', 'wrong_setup_command', run_name='__not_main__')
        with self.assertRaises(SystemExit):
            run_module('setup', 'wrong_setup_command')
