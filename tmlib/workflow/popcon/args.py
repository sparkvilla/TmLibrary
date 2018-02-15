# TmLibrary - TissueMAPS library for distibuted image analysis routines.
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
from tmlib.workflow.args import Argument
from tmlib.workflow.args import BatchArguments
from tmlib.workflow.args import SubmissionArguments
from tmlib.workflow import register_step_batch_args
from tmlib.workflow import register_step_submission_args


@register_step_batch_args('popcon')
class PopConBatchArguments(BatchArguments):

    extract_object = Argument(
        type=str, short_flag='e', 
        help='Object that should be processed, e.g. Nuclei'
    )
 
    assign_object  = Argument(
        type=str, short_flag='a', 
        help='Object that the extract_object get assigned to, e.g. Cells'
    )


    batch_size = Argument(
        type=int, help='number of wells that should be processed per job',
        default=100, flag='batch-size', short_flag='b'
    )


@register_step_submission_args('popcon')
class PopConSubmissionArguments(SubmissionArguments):

    pass
