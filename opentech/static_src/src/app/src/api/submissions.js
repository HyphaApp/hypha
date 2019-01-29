import { apiFetch } from '@api/utils';

export async function fetchSubmissionsByRound(id) {
    return apiFetch('/apply/api/submissions/', 'GET', {
        'round': id,
        'page_size': 1000,
    });
}


export async function fetchSubmission(id) {
    return apiFetch(`/apply/api/submissions/${id}/`, 'GET');
}
