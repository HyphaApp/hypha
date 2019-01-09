import React from 'react';
import SubmissionsByRoundList from '@components/SubmissionsByRoundList';

export default class SubmissionsByRoundContainer extends React.Component {
    render() {
        const mockItems = [
            {
                title: "Test stage 1",
                applications: [],
            },
            {
                title: "Test stage 2 blabla",
                applications: [],
            },
        ];
        return (
            <>
                <SubmissionsByRoundList items={mockItems} />
            </>
        );
    }
}
