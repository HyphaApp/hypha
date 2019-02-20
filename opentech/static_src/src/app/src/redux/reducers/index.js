import { combineReducers } from 'redux'

import submissions from '@reducers/submissions';
import rounds from '@reducers/rounds';
import notes from '@reducers/notes';
import messages from '@reducers/messages';

export default combineReducers({
    messages,
    notes,
    submissions,
    rounds,
});
