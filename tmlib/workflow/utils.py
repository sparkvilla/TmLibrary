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
import logging
import datetime
import numpy as np
from prettytable import PrettyTable

import gc3libs
from gc3libs.quantity import Memory
from gc3libs.session import Session
from gc3libs.url import Url
from gc3libs.persistence.sql import make_sqlstore

import tmlib.models as tm
from tmlib.models.utils import get_db_uri

logger = logging.getLogger(__name__)


def create_gc3pie_sql_store():
    '''Creates a `Store` instance for job persistence in the PostgreSQL table
    :class:`Tasks <tmlib.models.submission.Tasks>`.

    Returns
    -------
    gc3libs.persistence.sql.SqlStore
        `GC3Pie` store

    Warning
    -------
    The "tasks" table must already exist.
    '''
    def get_time(task, time_attr):
        def get_recursive(_task, duration):
            if hasattr(_task, 'tasks'):
                d = np.sum([
                    get_recursive(t, duration) for t in _task.tasks
                ])
                if d == 0.0:
                    return None
                else:
                    return d
            else:
                return getattr(_task.execution, time_attr).to_timedelta()
        return get_recursive(task, datetime.timedelta(seconds=0))

    logger.info('create GC3Pie store using "tasks" table')
    db_uri = get_db_uri()
    store_url = Url(db_uri)
    table_columns = tm.Task.__table__.columns
    return make_sqlstore(
        url=store_url,
        table_name='tasks',
        extra_fields={
            table_columns['name']:
                lambda task: task.jobname,
            table_columns['exitcode']:
                lambda task: task.execution.exitcode,
            table_columns['time']:
                lambda task: get_time(task, 'duration'),
            table_columns['memory']:
                lambda task: task.execution.max_used_memory.amount(Memory.MB),
            table_columns['cpu_time']:
                lambda task: get_time(task, 'used_cpu_time'),
            table_columns['submission_id']:
                lambda task: task.submission_id,
            table_columns['is_collection']:
                lambda task: hasattr(task, 'tasks'),
            table_columns['type']:
                lambda task: type(task).__name__
        }
    )


def create_gc3pie_session(location, store):
    '''Creates a `Session` instance for job persistence in the PostgresSQL table

    Parameters
    ----------
    location: str
        path to a directory on disk for the file system representation of the
        store
    store: gc3libs.persistence.store.Store
        store instance

    Returns
    -------
    gc3libs.persistence.session.Session
        `GC3Pie` session
    '''
    logger.info('create GC3Pie session')
    # NOTE: Unfortunately, we cannot parse the store instance to the constructor
    # of Session.
    return Session(location, store=store)


def create_gc3pie_engine(store, forget=False):
    '''Creates an `Engine` instance for submitting jobs for parallel
    processing.

    Parameters
    ----------
    store: gc3libs.persistence.store.Store
        GC3Pie store object
    forget: bool, optional
        whether tasks in state ``TERMINATED`` should be automatically
        removed from the engine

    Returns
    -------
    gc3libs.core.Engine
        engine
    '''
    logger.info('create GC3Pie engine')
    n = 1000  # NOTE: match with number of db connections!!!
    logger.debug('set maximum number of submitted jobs to %d', n)
    engine = gc3libs.create_engine(
        store=store, max_in_flight=n, max_submitted=n, forget_terminated=forget
    )
    # Put all output files in the same directory
    logger.debug('store stdout/stderr in common output directory')
    engine.retrieve_overwrites = True
    return engine


def format_stats_data(stats):
    '''For each task state (and pseudo-state like ``ok`` or
    ``failed``), two values are returned: the count of managed
    tasks that were in that state when `Engine.progress()` was
    last run, and what percentage of the total managed tasks this
    is.

    Parameters
    ----------
    stats: gc3libs.core.Engine
        as returned by :meth:`gc3libs.core.Engine.stats()`

    Returns
    -------
    dict
        global statistics about the jobs in the :class:`Engine`
    '''
    data = {}
    tot = stats['total']
    for state, count in stats.items():
        data['count_' + state.lower()] = count
        data['percent_' + state.lower()] = 100.0 * count / max(tot, 1)
    return data


def format_timestamp(elapsed_time):
    '''Formats a timestamp in seconds to "HH:MM:SS" string.

    Parameters
    ----------
    elapsed_time: float
        elapsed time in seconds

    Returns
    -------
    str
        formatted timestamp
    '''
    return '{:d}:{:02d}:{:02d}'.format(
        *reduce(
            lambda ll, b: divmod(ll[0], b) + ll[1:],
            [(int(elapsed_time),), 60, 60]
        )
    )


def get_task_data_from_sql_store(task, recursion_depth=None):
    '''Provides the following data for each task and recursively for each
    subtask in form of a mapping:

        * ``id`` (*int*): id of task
        * ``submission_id`` (*int*): id of submission
        * ``name`` (*str*): name of task
        * ``state`` (*g3clibs.Run.State*): state of the task
        * ``live`` (*bool*): whether the task is currently processed
        * ``done`` (*bool*): whether the task is done
        * ``failed`` (*bool*): whether the task failed, i.e. terminated
          with non-zero exitcode
        * ``percent_done`` (*float*): percent of subtasks that are *done*
        * ``exitcode`` (*int*): status code returned by the program
        * ``time`` (*str*): duration as "HH:MM:SS"
        * ``memory`` (*float*): amount of used memory in MB
        * ``cpu_time`` (*str*): used cpu time as "HH:MM:SS"
        * ``type`` (*str*): type of the task object

    Parameters
    ----------
    task: gc3libs.workflow.TaskCollection or gc3libs.Task
        submitted highest level GC3Pie task
    recursion_depth: int, optional
        recursion depth for subtask querying; by default
        data of all subtasks will be queried (default: ``None``)

    Returns
    -------
    dict
        information about each task and its subtasks
    '''
    def get_info(task_, i):
        data = dict()
        if recursion_depth is not None:
            if i > recursion_depth:
                return
        with tm.utils.MainSession() as session:
            if not hasattr(task_, 'persistent_id'):
                # If the task doesn't have a "persistent_id", it means that
                # it hasn't yet been inserted into the database table and
                # consequently hasn't yet been processed either.
                data = {
                    'done': False,
                    'failed': False,
                    'name': task_.name,
                    'state': task_.execution.state,
                    'live': False,
                    'memory': None,
                    'type': type(task_).__name__,
                    'exitcode': None,
                    'id': None,
                    'submission_id': task_.submission_id,
                    'time': None,
                    'cpu_time': None
                }
            else:
                task_info = session.query(tm.Task).get(task_.persistent_id)
                data = task_info.status
            if hasattr(task_, 'tasks'):
                done = 0.0
                for t in task_.tasks:
                    if hasattr(t, 'persistent_id'):
                        t_info = session.query(tm.Task).get(t.persistent_id)
                        if t_info.state == gc3libs.Run.State.TERMINATED:
                            done += 1
                if len(task_.tasks) > 0:
                    data['percent_done'] = done / len(task_.tasks) * 100
                else:
                    data['percent_done'] = 0
            else:
                if task_info.state == gc3libs.Run.State.TERMINATED:
                    data['percent_done'] = 100
                else:
                    data['percent_done'] = 0

            if hasattr(task_, 'tasks'):
                data['n_subtasks'] = len(task_.tasks)
                data['subtasks'] = [get_info(t, i+1) for t in task_.tasks]
            else:
                data['n_subtasks'] = 0
                data['subtasks'] = []

        return data

    if task is None:
        return None
    else:
        return get_info(task, 0)


def print_task_status(task_data):
    '''Pretty prints the status of a submitted GC3Pie tasks to the console in
    table format.

    Parameters
    ----------
    task_data: dict
        information about each task and its subtasks

    See also
    --------
    :func:`tmlib.workflow.utils.get_task_data_from_sql_store`
    '''
    def add_row_recursively(data, table, i):
        table.add_row([
            data['name'],
            data['type'],
            data['state'],
            '%.2f' % data['percent_done'],
            data['exitcode'] if data['exitcode'] is not None else '',
            data['time'] if data['time'] is not None else '',
            data['memory'] if data['memory'] is not None else '',
            data['cpu_time'] if data['cpu_time'] is not None else '',
            data['id']
        ])
        for subtd in data.get('subtasks', list()):
            if subtd is None:
                continue
            add_row_recursively(subtd, table, i+1)
    x = PrettyTable([
            'Name', 'Type', 'State', 'Done (%)', 'ExitCode',
            'Time (HH:MM:SS)', 'Memory (MB)', 'CPU Time (HH:MM:SS)', 'ID'
    ])
    x.align['Name'] = 'l'
    x.align['Type'] = 'l'
    x.align['State'] = 'l'
    x.align['Done (%)'] = 'r'
    x.align['Memory (MB)'] = 'r'
    x.align['ID'] = 'r'
    x.padding_width = 1
    add_row_recursively(task_data, x, 0)
    print x


def log_task_status(task_data, logger, monitoring_depth):
    '''Logs the status of a submitted GC3Pie task.

    Parameters
    ----------
    task_data: dict
        information about each task and its subtasks
    logger: logging.Logger
        configured logger instance
    monitoring_depth: int
        recursion depth for subtask querying
    '''
    def log_recursive(data, i):
        logger.info(
            '%s: %s (%.2f %%)',
            data['name'], data['state'], data['percent_done']
        )
        if i < monitoring_depth:
            for subtd in data.get('subtasks', list()):
                log_recursive(subtd, i+1)
    log_recursive(task_data, 0)


def log_task_failure(task_data, logger):
    '''Logs the failure of a submitted GC3Pie task.

    Parameters
    ----------
    task_data: dict
        information about each task and its subtasks
    logger: logging.Logger
        configured logger instance
    '''
    def log_recursive(data, i):
        if data['failed']:
            logger.error(
                '%s (id: %s) failed with exitcode %s',
                 data['name'], data['id'], data['exitcode']
            )
        for subtd in data.get('subtasks', list()):
            log_recursive(subtd, i+1)
    log_recursive(task_data, 0)