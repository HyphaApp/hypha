export function fetchRound(id) {
    return {
        path:`/v1/rounds/${id}/`,
    };
}

export function fetchRounds() {
    return {
        path:`/v1/rounds/`,
        params: {
            page_size: 1000,
        },
    };
}
