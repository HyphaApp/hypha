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
