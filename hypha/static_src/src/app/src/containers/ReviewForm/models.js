import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  metaStructure : null,
  loading : true,
  initialValues : null,
  saveAsDraft: false
});

export default initialState;
