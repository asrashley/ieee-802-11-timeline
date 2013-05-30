#############################################################################
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
#############################################################################
#
#  Project Name        :    IEEE 802.11 Timeline Tool#                                                                            *
#
#  Author              :    Alex Ashley
#
#############################################################################

''' Delete all objects from a model, or all objects from a query
'''
def bulk_delete(model, query=None):
    if query is None:
        query = model.objects.all()
    pks = query.values_list('pk',flat=True)
    while pks:
        batch = pks[:30]
        pks = pks[30:]
        model.objects.filter(pk__in=batch).delete()