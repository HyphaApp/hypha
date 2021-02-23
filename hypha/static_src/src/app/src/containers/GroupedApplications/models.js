import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  loading : true,
  applications: {},
  filterQuery : null
});

export default initialState;
