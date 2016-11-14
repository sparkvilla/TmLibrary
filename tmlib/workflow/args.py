# TmLibrary - TissueMAPS library for distibuted image analysis routines.
# Copyright (C) 2016  Markus D. Herrmann, University of Zurich and Robin Hafen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
import re
import types
import logging
import inspect
import argparse
from abc import ABCMeta

from tmlib.utils import assert_type

logger = logging.getLogger(__name__)


def _check_dependency(required_arg, required_value=None):
    class ArgumentDependencyAction(argparse.Action):
        def __call__(self, parser, namespace, values, option_string=None):
            if getattr(namespace, required_arg) is None:
                parser.error(
                    'Argument "%s" also requires "%s".' % (
                        self.dest, required_arg
                    )
                )
            if required_value is not None:
                if getattr(namespace, required_arg) != required_value:
                    parser.error(
                        'Argument "%s" can only be used when value of '
                        '"%s" is %s.' % (
                            self.dest, required_arg, str(required_value)
                        )
                    )
            setattr(namespace, self.dest, values)
    return ArgumentDependencyAction



class Argument(object):

    '''Descriptor class for an argument.'''

    @assert_type(
        type='type', help='basestring',
        choices=['set', 'list', 'types.NoneType'],
        flag=['basestring', 'types.NoneType'],
        dependency=['tuple'],
        meta=['basestring', 'types.NoneType']
    )
    def __init__(self, type, help, default=None, choices=None, flag=None,
            required=False, disabled=False, get_choices=None, meta=None,
            dependency=()):
        '''
        Parameters
        ----------
        type: type
            type of the argument
        help: str
            help message that describes the argument
        default: , optional
            default value (default: ``None``)
        choices: set or list or function, optional
            choices for value
        flag: str, optional
            single letter that serves as a flag for command line usage
            (default: ``None``)
        required: bool, optional
            whether the argument is required (default: ``False``)
        disabled: bool, optional
            whether the argument should be disabled in the UI
            (default: ``False``)
        get_choices: function, optional
            function that takes an object
            of type :class:`Experiment <tmlib.models.experiment.Experiment>`
            and returns the choices in case they need to (and can) be determined
            dynamically (default: ``None``)
        meta: str, optional
            alternative name of the argument displayed for command line options
        dependency: tuple, optional
            name-value pair of an argument the given argument depends on

        Note
        ----
        Automatically adds a docstring in NumPy style to the instance based on 
        the values of `type` and `help`.

        Warning
        -------
        Value of `flag` must be unique within an argument collection,
        otherwise this will lead to conflicts in parsing of the arguments.
        '''
        self.type = type
        self.help = help
        self.required = required
        self.disabled = disabled
        self.default = default
        self.value = None
        if isinstance(get_choices, types.FunctionType):
            arg_names = inspect.getargspec(get_choices).args
            if len(arg_names) > 1:
                raise ValueError(
                    'Function "%s" for getting argument choices must only have '
                    'a single argument.' % get_choices.__name__
                )
            self.get_choices = get_choices
        self.meta = meta
        if self.default is not None:
            if self.type == str:
                if not isinstance(self.default, basestring):
                    raise TypeError(
                        'Argument "default" must have type basestring.'
                    )
            else:
                if not isinstance(self.default, self.type):
                    raise TypeError(
                        'Argument "default" must have type %s.'
                        % self.type.__name__
                    )
            self.required = False
            self.value = self.default
        self.choices = choices
        if self.choices is not None:
            self.choices = set(choices)
            if self.type == str:
                if not all([isinstance(c, basestring) for c in self.choices]):
                    raise TypeError(
                        'Elements of argument "choices" must have type '
                        'basestring.'
                    )
            else:
                if not all([isinstance(c, self.type) for c in self.choices]):
                    raise TypeError(
                        'Elements of argument "choices" must have type %s.'
                        % self.type.__name__
                    )
        else:
            if self.type == bool:
                self.choices = {True, False}
        if flag is not None:
            if not(flag.isalpha() and len(flag) == 1):
                raise ValueError('Argument "flag" must be a letter.')
        self.flag = flag
        formatted_help_message = self.help.replace('\n', ' ').split(' ')
        formatted_help_message[0] = formatted_help_message[0].lower()
        formatted_help_message = ' '.join(formatted_help_message)
        if len(dependency) > 2:
            raise ValueError(
                'Dependency must be a single name-value pair.'
            )
        self.dependency = dependency
        self.__doc__ = '%s: %s' % (self.type.__name__, formatted_help_message)

    @property
    def name(self):
        '''str: name of the argument'''
        return self._name

    @name.setter
    def name(self, value):
        if not isinstance(value, str):
            raise TypeError('Attribute "name" must have type str.')
        if re.search(r'[^a-z_]', value):
            raise ValueError(
                'Attribute "name" must be lower case and only contain letters '
                '(a-z) or underscores (_).'
            )
        self._name = value

    @property
    def _attr_name(self):
        return '_%s' % self.name

    def __get__(self, instance, owner):
        # Allow only instances of a class to get the value, i.e.
        # when accessed as an instance attribute, but return
        # the instance of the Argument class if accessed
        # as a class attribute
        if instance is None:
            return self
        logger.debug(
            'get argument "%s" from attribute "%s" of instance of class "%s"',
            self.name, self._attr_name, instance.__class__.__name__
        )
        if not hasattr(instance, self._attr_name):
            if self.required:
                raise AttributeError(
                    'Argument "%s" is required.' % self.name
                )
            setattr(instance, self._attr_name, self.default)
        return getattr(instance, self._attr_name)

    def __set__(self, instance, value):
        logger.debug(
            'set argument "%s" as attribute "%s" of instance of class "%s"',
            self.name, self._attr_name, instance.__class__.__name__
        )
        if self.type == str:
            if not isinstance(value, basestring) and value is not None:
                raise TypeError(
                    'Argument "%s" must have type basestring.'
                )
        elif self.type == float:
            # Workaround decimal Javascript issue
            value = float(value)
        else:
            if not isinstance(value, self.type) and value is not None:
                raise TypeError(
                    'Argument "%s" must have type %s.'
                    % (self.name, self.type.__name__)
                )
        setattr(instance, self._attr_name, value)

    def add_to_argparser(self, parser):
        '''Adds the argument to an argument parser for use in a command line
        interface.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            argument parser

        Returns
        -------
        argparse.ArgumentParser
            `parser` with added arguments
        '''
        # flags = [self.name]
        flags = ['--%s' % self.name]
        kwargs = dict()
        if self.flag is not None:
            flags.append('-%s' % self.flag)
        kwargs['dest'] = self.name
        kwargs['help'] = re.sub(r'\s+', ' ', self.help).strip()
        if self.type == bool:
            if self.default:
                kwargs['action'] = 'store_false'
            else:
                kwargs['action'] = 'store_true'
        else:
            kwargs['type'] = self.type
            kwargs['default'] = self.default
            kwargs['choices'] = self.choices
            if self.default is not None:
                kwargs['help'] += ' (default: %s)' % self.default
        kwargs['required'] = self.required
        if len(self.dependency) > 0:
            k = self.dependency[0]
            try:
                v = self.dependency[1]
            except IndexError:
                v = None
            kwargs['action'] = _check_dependency(k, v)
        if self.meta is not None:
            kwargs['metavar'] = self.meta.upper()
        parser.add_argument(*flags, **kwargs)

def __str__(self):
    return '<Argument(name=%r, type=%r)>' % (self.name, self.type)


class _ArgumentMeta(ABCMeta):

    '''Metaclass for adding class attributes of type
    :class:`Argument <tmlib.workflow.args.Argument>` as descriptors to instances of
    the class.
    '''

    def __init__(cls, clsname, bases, attrs):
        super(_ArgumentMeta, cls).__init__(clsname, bases, attrs)
        for name, value in attrs.iteritems():
            if isinstance(value, Argument):
                argument = value
                argument.name = name

    def __call__(cls, *args, **kwargs):
        logger.debug(
            'pass arguments to constructor of class "%s"', cls.__name__
        )
        return ABCMeta.__call__(cls, *args, **kwargs)


class ArgumentCollection(object):

    '''Abstract base class for an argument collection. The collection serves
    as a container for arguments that can be parsed to methods of
    :class:`CommandLineInterface <tmlib.workflow.cli.CommandLineInterface>`
    decorated with :func:`climethod <tmlib.workflow.climethod>`.

    Implementations of the class can be instantiated without having to
    implement a constructor, i.e. an `__init__` method. The constructor
    accepts keyword arguments and strips the values from those arguments
    that are implemented as class attributes with type
    :class:`Argument <tmlib.workflow.args.Argument>` and replaces any default
    values. When there is no default value specified, the argument has to be
    provided as a key-value pair. Derived classes can explicitly implement
    a constructor if required.
    '''

    __metaclass__ = _ArgumentMeta

    def __init__(self, **kwargs):
        '''
        Parameters
        ----------
        **kwargs: dict, optional
            keyword arguments to overwrite
        '''
        for name in dir(self):
            value = getattr(self.__class__, name)
            if isinstance(value, Argument):
                if name in kwargs:
                    setattr(self, name, kwargs[name])

    @property
    def help(self):
        '''str: brief description of the collection or the method to which
        the arguments should be passed
        '''
        return self._help

    @help.setter
    def help(self, value):
        if not isinstance(value, basestring):
            raise TypeError('Attribute "help" must have type basestring.')
        self._help = value

    @property
    def docstring(self):
        '''str: docstring in NumPy style for the method to which the arguments
        should be passed; build based on the value of the `help` attribute
        and those of the `type` and `help` attributes of individual arguments
        '''
        formatted_help_message = self.help.replace('\n', ' ').split()
        formatted_help_message[0] = formatted_help_message[0].capitalize()
        formatted_help_message = ' '.join(formatted_help_message)
        formatted_help_message += '.'
        docstring = '%s\n\nParameters\n----------\n' % formatted_help_message
        for name in dir(self):
            if name.startswith('_'):
                continue
            value = getattr(self.__class__, name)
            if isinstance(value, Argument):
                docstring += '%s: %s' % (name, value.type.__name__)
                if value.default is not None:
                    docstring += ', optional\n'
                else:
                    docstring += '\n'
                docstring += '    %s' % value.help
                if value.default is not None:
                    docstring += ' (default: ``%r``)\n' % value.default
                else:
                    docstring += '\n'

    @classmethod
    def iterargs(cls):
        '''Iterates over the class attributes of type
        :class:`Argument <mlib.workflow.arg.Argument>`.

        Warning
        -------
        The value of the attribute `value` will be the default and not the one
        set on an instance of the class.
        '''
        for name in dir(cls):
            if name.startswith('_'):
                continue
            value = getattr(cls, name)
            if isinstance(value, Argument):
                yield value

    def iterargitems(self):
        '''Iterates over the argument items stored as attributes of the
        instance.
        '''
        for name in dir(self):
            if name.startswith('_'):
                continue
            value = getattr(self.__class__, name)
            if isinstance(value, Argument):
                yield (name, getattr(self, name))

    def add_to_argparser(self, parser):
        '''Adds each argument to an argument parser for use in a command line
        interface.

        Parameters
        ----------
        parser: argparse.ArgumentParser
            argument parser

        Returns
        -------
        argparse.ArgumentParser
            `parser` with added arguments
        '''
        for name in dir(self):
            if name.startswith('__'):
                continue
            value = getattr(self.__class__, name)
            if isinstance(value, Argument):
                value.add_to_argparser(parser)
        return parser

    def as_list(self):
        '''Returns class attributes of type
        :class:`Argument <tmlib.workflow.args.Argument>` as an array of
        key-value pairs.

        Returns
        -------
        List[dict]
            description of each argument
        '''
        description = list()
        for arg in self.iterargs():
            argument = {
                'name': arg.name,
                'help': re.sub(r'\s+', ' ', arg.help).strip(),
                'default': arg.default,
                'type': arg.type.__name__,
                'required': arg.required,
                'disabled': arg.disabled
            }
            try:
                argument['value'] = getattr(self, arg.name)
            except AttributeError:
                # Even if the attribute is required, we want to seriablize
                # the argument collection
                argument['value'] = None
            if arg.choices is not None:
               argument['choices'] = list(arg.choices)
            else:
                argument['choices'] = None
            description.append(argument)
        return description

    @assert_type(collection='tmlib.workflow.args.ArgumentCollection')
    def union(self, collection):
        '''Adds all arguments contained in another `collection`.

        Parameters
        ----------
        collection: tmlib.workflow.args.ArgumentCollection
            collection of arguments that should be added
        '''
        for name in dir(collection):
            if name.startswith('__'):
                continue
            value = getattr(self.__class__, name)
            if isinstance(value, Argument):
                setattr(self.__class__, name, value)


class BatchArguments(ArgumentCollection):

    '''Base class for arguments that are used to define how the
    computational task should be devided into individual batch jobs
    for parallel processing on the cluster.

    These arguments can be passed to a step-specific implementation of the
    :meth:`init <tmlib.workflow.cli.CommandLineInterface.init>` *CLI* method
    and will be parsed to the
    :meth:`create_batches <tmlib.workflow.api.ClusterRoutines.create_batches>`
    *API* method.

    Note
    ----
    Each workflow step must implement this class and add the arguments that
    the user should be able to set.
    '''


class SubmissionArguments(ArgumentCollection):

    '''Base class for arguments that are used to control the submission of
    jobs to the cluster.

    These arguments can be passed to a step-specific implementation of the
    :meth:`submit <tmlib.workflow.cli.CommandLineInterface.submit>` *CLI* 
    method and are parse to the
    :meth:`create_jobs <tmlib.workflow.api.ClusterRoutines.create_jobs>` *API*
    method.

    Note
    ----
    Each workflow step must implement this class and potentially override
    the provided defaults depending on the requirements of the jobs.

    '''

    duration = Argument(
            type=str, default='02:00:00', meta='HH:MM:SS',
        help='''
            walltime that should be allocated to a each "run" job
            in the format "HH:MM:SS"
        '''
    )

    memory = Argument(
        type=int, default=3800, meta='MB',
        help='''
            amount of memory that should be allocated to each "run" job
            in megabytes (MB)
        '''
    )

    cores = Argument(
        type=int, default=1, meta='NUMBER',
        help='''
            number of cores that should be allocated to each "run" job
        '''
    )


class ExtraArguments(ArgumentCollection):

    '''Collection of arguments that can be passed to the constructor of
    a step-specific implementation of the
    :class:`ClusterRoutines <tmlib.workflow.api.ClusterRoutines>` *API* class.

    Note
    ----
    A step may only implement this class when required.
    '''


class CliMethodArguments(ArgumentCollection):

    '''Collection of arguments that can be passed to a method of
    a step-specific implemenation of
    :class:`CommandLineInterface <tmlib.workflow.cli.CommandLineInterface>`,
    which are decoreated with :func:`climethod <tmlib.workflow.climethod>`.
    '''
