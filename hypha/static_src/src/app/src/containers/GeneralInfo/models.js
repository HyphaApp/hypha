import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  user : null,
  loading : true,
  userHasReview: false
});

export default initialState;
