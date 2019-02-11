import { combineReducers } from 'redux'

import submissions from '@reducers/submissions';
import rounds from '@reducers/rounds';
import notes from '@reducers/notes';

export default combineReducers({
    notes,
    submissions,
    rounds,
});
