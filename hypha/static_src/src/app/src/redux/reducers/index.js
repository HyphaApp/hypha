import { combineReducers } from 'redux'
import { connectRouter } from 'connected-react-router'

import submissions from '@reducers/submissions';
import rounds from '@reducers/rounds';
import notes from '@reducers/notes';
import messages from '@reducers/messages';
import statuses from '@reducers/statuses';
import { createBrowserHistory } from 'history';


export const history = createBrowserHistory();

export default (injectedReducers = {}) => {
  const rootReducer = combineReducers({
      router: connectRouter(history),
      notes,
      messages,
      rounds,
      statuses,
      submissions,
      ...injectedReducers
  });

  return rootReducer
}
