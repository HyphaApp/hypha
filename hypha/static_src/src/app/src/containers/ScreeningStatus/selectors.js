import {createSelector} from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
    state.ScreeningStatusContainer ? state.ScreeningStatusContainer : initialState;

export const selectScreeningInfo = createSelector(selectFieldsRenderer, domain => domain);

export const getScreeningLoading = createSelector(selectFieldsRenderer, domain => domain.loading);

export const selectScreeningStatuses = createSelector(selectFieldsRenderer, domain => domain.screeningStatuses
);

export const selectDefaultOptions = createSelector(selectScreeningStatuses, screeningStatuses => {
    return {
        yes: screeningStatuses && screeningStatuses.find((status) => status.default && status.yes),
        no: screeningStatuses && screeningStatuses.find((status) => status.default && !status.yes)
    };
});

export const selectVisibleOptions = createSelector(selectScreeningStatuses, selectScreeningInfo,
    (screeningStatuses, screeningInfo) =>
        screeningStatuses && screeningInfo.defaultSelectedValue &&
  screeningStatuses.filter((status) => status.yes === screeningInfo.defaultSelectedValue.yes &&
  status.id != screeningInfo.defaultSelectedValue.id).map((option) => {
      return {
          ...option,
          selected: screeningInfo.selectedValues.some((value) => value.id == option.id)
      };
  })
);
