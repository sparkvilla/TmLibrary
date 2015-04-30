#!/usr/bin/env python
import os
import os.path as osp
import time
import datetime
import yaml
import glob
import argparse
from subprocess32 import call, check_call

'''
Brutus submission script for stk to png conversion.

Automatically generates a custom config file and joblist files.

'''

config = {
    'nomenclature_string': '{project}_s{site}_r{row}_c{column}_{filter}_C{channel}.png',
    'nomenclature_format': {
        'project': '%s',
        'site': '%.4d',
        'row': '%.2d',
        'column': '%.2d',
        'filter': '%s',
        'channel': '%.2d',
    },
    'acquisition_mode': 'ZigZagHorizontal',
    'acquisition_layout': 'columns>rows'
}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Brutus submission script '
                                     'for .stk to .png image conversion')

    parser.add_argument('project_dir', nargs='?',
                        help='path to the project folder')

    parser.add_argument('-b', '--batch_size', dest='batch_size',
                        type=int, default=20,
                        help='number of "jobs" that are submitted per batch')

    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    input_dir = osp.join(project_dir, 'STK')
    batch_size = args.batch_size

    lsf_dir = osp.join(project_dir, 'lsf')
    if not osp.exists(lsf_dir):
        print '. creating "lsf" output directory'
        os.mkdir(lsf_dir)

    # Create custom config.yaml file
    config_file = osp.join(lsf_dir, 'visi_custom.config')
    with open(config_file, 'w') as f:
        # Write it in safe mode
        f.write(yaml.safe_dump(config, default_flow_style=False,
                default_style='"'))

    # Shall we kill previous 'joblist' files?

    print '. creating joblist files'
    joblists_dir = osp.join(lsf_dir, 'joblists')
    if not osp.exists(joblists_dir):
        os.mkdir(joblists_dir)
    command = ['visi', '-o', joblists_dir, '--joblist']
    files = glob.glob(osp.join(input_dir, '*'))
    check_call(command + files)

    joblist_files = glob.glob(osp.join(joblists_dir, '*.joblist'))

    if not joblist_files:
        raise Exception('Could not find any .joblist files.')

    for joblist_file in joblist_files:

        print '. processing joblist from file "%s"' % joblist_file

        subproject_name = osp.splitext(osp.basename(joblist_file))[0]

        batch_files = glob.glob(osp.join(input_dir, '%s*' % subproject_name))

        joblist_content = yaml.load(open(joblist_file).read())

        jobs = map(int, joblist_content.keys())
        number_of_jobs = len(joblist_content)
        number_of_batches = number_of_jobs / batch_size

        for batch in xrange(number_of_batches + 2):

            if batch == 0:
                continue
            lower = batch * batch_size - batch_size
            upper = batch * batch_size - 1
            if upper > number_of_jobs:
                upper = number_of_jobs - 1
            batch_range = '%s-%s' % (jobs[lower], jobs[upper])

            ts = time.time()
            st = datetime.datetime.fromtimestamp(ts).strftime('%Y-%m-%d_%H-%M-%S')
            lsf = osp.join(project_dir, 'lsf', 'visi_%s_%.5d_%s_%s.lsf' %
                           (subproject_name, batch, batch_range, st))

            print '. submitting job %d' % batch
            call(['bsub', '-W', '8:00', '-o', lsf,
                 '-R', 'rusage[mem=4000,scratch=4000]',
                 'visi', '--rename', '--split_output',
                 '--batch', '%s' % batch_range,
                 '--config', config_file] + batch_files)