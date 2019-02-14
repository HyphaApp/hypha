import { combineReducers } from 'redux'
import { connectRouter } from 'connected-react-router'

import submissions from '@reducers/submissions';
import rounds from '@reducers/rounds';
import notes from '@reducers/notes';
import messages from '@reducers/messages';

export default combineReducers({
    router: connectRouter(history),
    notes,
    messages,
    submissions,
    rounds,
});
