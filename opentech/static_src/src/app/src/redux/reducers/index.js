import { combineReducers } from 'redux'

import submissions from '@reducers/submissions';
import rounds from '@reducers/rounds';

export default combineReducers({
    submissions,
    rounds,
});
