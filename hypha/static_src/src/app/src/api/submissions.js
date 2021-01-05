export function fetchSubmissionsByRound(id, filters) {
    const params = new URLSearchParams
    params.append('page_size', 1000) 
    params.append('round', id) 

    if(filters){
        filters.forEach(filter => 
            {   
                if(filter.key == 'status'){
                    filter.value.map(values =>
                        values.map(value =>
                            params.append(filter.key, value)))
                }else{
                    filter.value.forEach(filterValue => 
                    params.append(filter.key,filterValue))
                }
            }
            )
    }
    return {
        path:'/v1/submissions/',
        params
    };
}

export function fetchSubmission(id) {
    return {
        path: `/v1/submissions/${id}/`,
    };
}

export function fetchReviewDraft(id) {
    return {
        path: `/v1/submissions/${id}/reviews/draft/`,
    };
}

export function fetchDeterminationDraft(id) {
    return {
        path: `/v1/submissions/${id}/determinations/draft/`,
    };
}

export function fetchSubmissionsByStatuses(statuses, filters) {
    const params = new URLSearchParams
    params.append('page_size', 1000)
    statuses.forEach(v => params.append('status', v));
    
    if(filters){
        filters.forEach(filter => 
            {   
                if(filter.key == 'status'){
                    filter.value.map(values =>
                        values.map(value =>
                            params.append(filter.key, value)))
                }else{
                    filter.value.forEach(filterValue => 
                    params.append(filter.key,filterValue))
                }
            }
            )
    }
    return {
        path:'/v1/submissions/',
        params,
    };
}

export function executeSubmissionAction(submissionID, action) {
    return {
        path: `/v1/submissions/${submissionID}/actions/`,
        method: 'POST',
        options: {
            body: {
                action,
            }
        }
    }
}
