from models import Ballot
from dbindexer.lookups import StandardLookup
from dbindexer.api import register_index

#register_index(Ballot, {'project': StandardLookup(),
#})