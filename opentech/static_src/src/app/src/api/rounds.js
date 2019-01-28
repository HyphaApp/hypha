import { apiFetch } from '@api/utils';

export async function fetchRound(id) {
    return apiFetch(`/apply/api/rounds/${id}`, 'GET');
}
