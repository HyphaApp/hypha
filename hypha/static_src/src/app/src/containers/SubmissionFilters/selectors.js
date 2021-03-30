import { createSelector } from 'reselect';
import initialState from './models';

export const selectFieldsRenderer = state =>
  state.SubmissionFiltersContainer ? state.SubmissionFiltersContainer : initialState;

export const SelectSubmissionFiltersInfo = createSelector(selectFieldsRenderer, domain => domain);

export const SelectSelectedFilters = createSelector(selectFieldsRenderer, domain => domain.filterQuery)

export const SelectFiltersToBeRendered = createSelector(selectFieldsRenderer, domain => {
  return domain.filters && domain.filters.map(filter => 
            {
              let modifiedFilter =  filter.asMutable()
              if(filter.filterKey === "status") {
                modifiedFilter.options = modifiedFilter.options.map(option => {
                  return {
                    ...option,
                    key: option.key.asMutable().sort().join(",")
                  }
                })
              }
              return modifiedFilter
})
})

