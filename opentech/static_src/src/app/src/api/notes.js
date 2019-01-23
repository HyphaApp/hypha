import { apiFetch } from '@api/utils';

export function fetchNotesForSubmission(submissionID, visibility = 'internal') {
    return apiFetch(`/apply/api/submissions/${submissionID}/comments/`, 'GET', {
        visibility,
        page_size: 1000,
    });
}


export function createNoteForSubmission(submissionID, note) {
    return apiFetch(`/apply/api/submissions/${submissionID}/comments/`, 'POST', {}, {
        body: JSON.stringify(note),
    });
}
