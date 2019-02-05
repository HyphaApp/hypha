export function fetchSubmissionsByRound(id) {
    return {
        path:'/apply/api/submissions/',
        params: {
            round: id,
            page_size: 1000,
        }
    };
}


export function fetchSubmission(id) {
    return {
        path: `/apply/api/submissions/${id}/`,
    };
}

export function fetchSubmissionsByStatuses(statuses) {
    const params = new URLSearchParams
    params.append('page_size', 1000)
    statuses.forEach(v => params.append('status', v));

    return {
        path:'/apply/api/submissions/',
        params,
    };
}
