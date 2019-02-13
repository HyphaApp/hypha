export function fetchNotesForSubmission(submissionID, visibility = 'internal') {
    return {
        path: `/apply/api/submissions/${submissionID}/comments/`,
        params: {
            visibility,
            page_size: 1000,
        }
    };
}


export function fetchNewNotesForSubmission(submissionID, latestID, visibility = 'internal') {
    return {
        path: `/apply/api/submissions/${submissionID}/comments/`,
        params: {
            visibility,
            newer: latestID,
            page_size: 1000,
        }
    };
}


export function createNoteForSubmission(submissionID, note) {
    return {
        path: `/apply/api/submissions/${submissionID}/comments/`,
        method: 'POST',
        options: {
            body: note,
        }
    };
}
