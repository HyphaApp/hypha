import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
  metaTermsStructure : null,
  loading : true,
  initialValues : null,
  selectedMetaTerms: []
});

export default initialState;
