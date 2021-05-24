import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  loading : true,
  defaultSelectedValue: null,
  screeningStatuses: null,
  selectedValues: null
});

export default initialState;
