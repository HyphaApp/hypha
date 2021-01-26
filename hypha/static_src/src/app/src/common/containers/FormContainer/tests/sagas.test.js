
// import * as Actions from "../actions";
// import { put, call, select } from "redux-saga/effects";
// import * as Sagas from "../sagas";
// import { apiFetch } from '@api/utils';
// import * as Selectors from "../selectors";


// describe("Test sagas in form container module", () => {

//   it("Check validate fields saga", () => {
    
//     const formsInfo =  {
//       "form1" : {
//         values : {
//           determination : "0",
//           message : "<p>asdasda</p>"
//         },
//         constraints: {
//           determination:{
//              presence: {
//               allowEmpty: false
//             }
//           }
//         }
//       }
//     }
//     const state = {
//       FormContainer : {
//         forms : formsInfo
//       }
//     }
//     const formId = "form1"
//     const action = Actions.validateAndSubmitFormAction(formId);
//     const generator = Sagas.validateFields(action);
//     expect(
//       generator.next().value
//     ).toEqual(
//       select(Selectors.selectFormsInfo)
//     );

    // expect(
    //   generator.next(formId).value
    // ).toEqual(
    //   put(Actions.clearValidationErrorAction(formId))
    // );
    // expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()))
    // expect(generator.next().done).toBeTruthy();
//   });

// })