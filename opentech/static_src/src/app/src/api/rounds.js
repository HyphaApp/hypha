import { apiFetch } from '@api/utils';

export function fetchRound(id) {
    return apiFetch(`/apply/api/rounds/${id}/`, 'GET');
}
