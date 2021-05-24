import * as Actions from "../actions";
import { put, call, delay, takeEvery } from "redux-saga/effects";
import * as Sagas from "../sagas";
import { apiFetch } from '@api/utils';
import {select} from 'redux-saga/effects';
import * as Selectors from '../selectors';
import homePageSaga from '../sagas';
import * as ActionTypes from '../constants';


describe("Test setDefaultValue in Screening status module", () => {

    it("Should trigger correct action for SUCCESS status", () => {
      const id = 1
      const data = "data"
      const action = Actions.selectDefaultValueAction(id, data);
      const generator = Sagas.setDefaultValue(action);
  
      expect(
        generator.next().value
      ).toEqual(
        put(Actions.showLoadingAction())
      );
  
      expect(generator.next().value).toEqual(call(
          apiFetch, 
          {
              path : `/v1/submissions/${id}/screening_statuses/default/`,
              method : "POST",
              options : {
                  body : JSON.stringify(data),
              }
          }
          )
      );
      const data1 = {id : 1}
      expect(generator.next({ json : () => data1}).value).toEqual(data1);
      expect(
        generator.next(data1).value
      ).toEqual(
        put(Actions.setDefaultSelectedAction(data1))
      );
      expect(
        generator.next(data1).value
      ).toEqual(put(Actions.setVisibleSelectedAction([])))
      expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()))
      expect(generator.next().done).toBeTruthy();
    });
    
    it("Should return false for id null", () => {
      const id = null
      const data = "data"
      const action = Actions.selectDefaultValueAction(id, data);
      const generator = Sagas.setDefaultValue(action);
      expect(generator.next().done).toBeTruthy();
    });
  
    it("Should tirgger correct action incase of error", () => {
      const id = 1
      const data = "data"
      const action = Actions.selectDefaultValueAction(id, data);
      const generator = Sagas.setDefaultValue(action);
      generator.next()
      expect(generator.throw(new Error()).value).toEqual(
        put(Actions.hideLoadingAction())
      );
      expect(generator.next().done).toBeTruthy();
    });
  
  });

describe("Test setVisibleOption in Screening status module", () => {

  it("Should trigger correct action for SUCCESS status", () => {
    const id = 1
    const data = {id : 2, title : "data"}
    const action = Actions.selectVisibleOptionAction(id, data);
    const generator = Sagas.setVisibleOption(action);

    expect(
      generator.next().value
    ).toEqual(
      delay(300)
    );

    expect(
      generator.next().value
    ).toEqual(
      put(Actions.showLoadingAction())
    );
    expect(
      generator.next().value
    ).toEqual(
      select(Selectors.selectScreeningInfo)
    );
    
    const screening = {
      selectedValues : [{id:1, title : 'one'}, {id:2, title : 'second'}]
    }
    expect(generator.next(screening).value).toEqual(call(
        apiFetch, 
        {
            path : `/v1/submissions/${id}/screening_statuses/${data.id}`,
            method : "DELETE"
        }
        )
    );
    expect(generator.next(screening).value).toEqual(put(Actions.setVisibleSelectedAction([{id:1, title : 'one'}])));
    expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()))
    expect(generator.next().done).toBeTruthy();
  });
  it("Should return false for id null", () => {
    const id = null
    const data = {id : 2, title : "data"}
    const action = Actions.selectVisibleOptionAction(id, data);
    const generator = Sagas.setVisibleOption(action);
    expect(generator.next().done).toBeTruthy();

  })
  it("Should trigger correct action for SUCCESS status2", () => {
    const id = 1
    const data = {id : 2, title : "data"}
    const action = Actions.selectVisibleOptionAction(id, data);
    const generator = Sagas.setVisibleOption(action);

    expect(
      generator.next().value
    ).toEqual(
      delay(300)
    );

    expect(
      generator.next().value
    ).toEqual(
      put(Actions.showLoadingAction())
    );
    expect(
      generator.next().value
    ).toEqual(
      select(Selectors.selectScreeningInfo)
    );
    
    const screening = {
      selectedValues : [{id:1, title : 'one', default : false}, {id:3, title : 'second', default : true}]
    }
    expect(generator.next(screening).value).toEqual(call(
        apiFetch, 
        {
            path : `/v1/submissions/${id}/screening_statuses/`,
            method : "POST",
            options : {
                body : JSON.stringify(data),
            }
        }
        )
    );
    const data1 = {id : 1}
    expect(generator.next({ json : () => data1}).value).toEqual(data1);
    expect(generator.next(screening.selectedValues).value).toEqual(put(Actions.setVisibleSelectedAction([{id:1, title : 'one', default : false}])));
    expect(generator.next().value).toEqual(put(Actions.hideLoadingAction()))
    expect(generator.next().done).toBeTruthy();
  });


  it("Should tirgger correct action incase of error", () => {
    const id = 1
    const data = "data"
    const action = Actions.selectVisibleOptionAction(id, data);
    const generator = Sagas.setVisibleOption(action);
    generator.next()
    expect(generator.throw(new Error()).value).toEqual(
      put(Actions.hideLoadingAction())
    );
    expect(generator.next().done).toBeTruthy();
  });

});

describe("Test takeEvery in Screening status module", () => {

  const genObject = homePageSaga();
  
  it('should wait for every SELECT_DEFAULT_VALUE action and call setDefaultValue', () => {
    expect(genObject.next().value)
      .toEqual(takeEvery(ActionTypes.SELECT_DEFAULT_VALUE,
        Sagas.setDefaultValue));
  });

  it('should wait for every SELECT_VISIBLE_OPTION action and call setVisibleOption', () => {
    expect(genObject.next().value)
      .toEqual(takeEvery(ActionTypes.SELECT_VISIBLE_OPTION,
        Sagas.setVisibleOption));
  });

});