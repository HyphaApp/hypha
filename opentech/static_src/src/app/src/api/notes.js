export function fetchNotesForSubmission(submissionID, visibility = 'team') {
    return {
        path: `/v1/submissions/${submissionID}/comments/`,
        params: {
            visibility,
            page_size: 1000,
        }
    };
}


export function fetchNewNotesForSubmission(submissionID, latestID, visibility = 'team') {
    return {
        path: `/v1/submissions/${submissionID}/comments/`,
        params: {
            visibility,
            newer: latestID,
            page_size: 1000,
        }
    };
}


export function createNoteForSubmission(submissionID, note) {
    return {
        path: `/v1/submissions/${submissionID}/comments/`,
        method: 'POST',
        options: {
            body: note,
        }
    };
}

export function editNoteForSubmission(note) {
    return {
        path: `/v1/comments/${note.id}/edit/`,
        method: 'POST',
        options: {
            body: JSON.stringify({ message: note.message }),
        }
    }
}
