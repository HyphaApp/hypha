export function fetchRound(id) {
    return {
        path:`/apply/api/rounds/${id}/`,
    };
}

export function fetchRounds() {
    return {
        path:`/apply/api/rounds/`,
        params: {
            page_size: 1000,
        },
    };
}
