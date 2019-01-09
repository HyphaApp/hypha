const initialState = {
    items: [
        {
            title: "Test stage 1",
            applications: [],
        },
        {
            title: "Test stage 2 blabla",
            applications: [],
        },
    ]
};

export default function submissions(state = initialState, action) {
    switch(action.type) {
        default:
            return state
    }
}
