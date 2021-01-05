import { createSelector } from 'reselect';


const getCurrentStatuses = state => state.statuses.current;

const getStatusesFetchingState = state => state.statuses.fetchingState;

const getSubmissionsByStatuses = state => state.statuses.byStatuses;


const getSubmissionIDsForCurrentStatuses = createSelector(
    [ getSubmissionsByStatuses, getCurrentStatuses ],
    (grouped, current) => {
        
        if (!current.length){
            let acc = []
            for (let status in grouped){
              acc = acc.concat(grouped[status])   
            }
            return acc
        }
        return current.reduce((acc, status) => acc.concat(grouped[status] || []), [])
    }
);

const getByStatusesError = createSelector(
    [ getStatusesFetchingState ],
    state => state.isErrored === true
);

const getByStatusesLoading = createSelector(
    [ getStatusesFetchingState ],
    state => state.isFetching === true
);

export {
    getCurrentStatuses,
    getByStatusesLoading,
    getByStatusesError,
    getSubmissionIDsForCurrentStatuses,
}
