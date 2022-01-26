import {selectFormsInfo, selectActiveForm} from '../selectors';
import initialState from '../models';


describe('Test the selector of form container', () => {

    it('Select Active form', () => {
        const state = {
            FormContainer: {
                activeForm: 'form1',
                forms: {id: 1, title: 'form1'}
            }
        };
        expect(selectActiveForm(state)).toEqual(state.FormContainer.activeForm);
    });

    it('Select forms info', () => {
        const state = {
            FormContainer: {
                activeForm: 'form1',
                forms: {id: 1, title: 'form1'}
            }
        };
        expect(selectFormsInfo(state)).toEqual(state.FormContainer.forms);
    });
}
);
