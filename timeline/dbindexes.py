from models import DenormalizedProjectBallots
from dbindexer.lookups import StandardLookup
from dbindexer.api import register_index

#register_index(DenormalizedProjectBallots, {'project__pk': StandardLookup(),
#})