# Import all models, in an order such that models only depend on
# models further up the list
# Why are the useless A = A lines here?  To keep flake8 happy!

from schedule.models.term import Term
Term = Term

from schedule.models.block import Block, BlockRangeRule
Block, BlockRangeRule = Block, BlockRangeRule

from schedule.models.location import Location
Location = Location

from schedule.models.show import Show, ShowType, ShowTextMetadata
Show, ShowType, ShowTextMetadata = Show, ShowType, ShowTextMetadata

from schedule.models.show import ShowLocation
ShowLocation = ShowLocation

from schedule.models.season import Season, SeasonTextMetadata
Season, SeasonTextMetadata = Season, SeasonTextMetadata

from schedule.models.timeslot import Timeslot, TimeslotTextMetadata
Timeslot, TimeslotTextMetadata = Timeslot, TimeslotTextMetadata

# This must go after the schedule entities, even though block must go
# before.  Confusing, eh?
from schedule.models.block_direct_rule import BlockShowRule
BlockShowRule = BlockShowRule

from schedule.models.credit import ShowCredit
ShowCredit = ShowCredit
