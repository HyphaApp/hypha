import React from 'react';
import SubmissionsByRoundListHeading from '@components/SubmissionsByRoundListHeading';


export default class SubmissionsByRoundList extends React.Component {
    renderListItems() {
        return this.props.items.map(v => {
            const applications = [];
            return (
                <>
                    <SubmissionsByRoundListHeading key="status-{v.title}" title={v.title} count={v.applications.length} />
                    <ul>
                        {applications}
                    </ul>
                </>
            );
        });
    }

    render() {
        return (
            <ul>
                {this.renderListItems()}
            </ul>
        );
    }
}
