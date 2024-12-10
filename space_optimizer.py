import selection
import pruning

# select important knobs then optimize their corresponding range
knob_list = selection.knob_select()
pruning.prune(knob_list)