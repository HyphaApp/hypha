export function fetchSubmissionsByRound(id) {
    return {
        path:'/v1/submissions/',
        params: {
            round: id,
            page_size: 1000,
        }
    };
}

export function fetchSubmission(id) {
    return {
        path: `/v1/submissions/${id}/`,
    };
}

export function fetchSubmissionsByStatuses(statuses) {
    const params = new URLSearchParams
    params.append('page_size', 1000)
    statuses.forEach(v => params.append('status', v));

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
