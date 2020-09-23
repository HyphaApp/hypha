import {createSelector} from 'reselect';
export const selectFormContainerDomain = state => state.FormContainer;

export const selectActiveForm = createSelector(
    selectFormContainerDomain,
    domain => domain.activeForm
);

export const selectFormsInfo = createSelector(
    selectFormContainerDomain,
    domain =>  domain.forms
);
