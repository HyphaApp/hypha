import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  loading : true,
  selectedFilters : {},
  filters: null,
  filterQuery : null
});

export default initialState;
