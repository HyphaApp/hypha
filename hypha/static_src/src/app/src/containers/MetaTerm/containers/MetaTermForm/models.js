import * as Immutable from 'seamless-immutable';

const initialState = Immutable.from({
    metaTermsStructure: null,
    loading: true,
    selectedMetaTerms: []
});

export default initialState;
