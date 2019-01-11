import React from 'react';
import SubmissionsByRoundListHeading from '@components/SubmissionsByRoundListHeading';
import SubmissionsByRoundListItem from '@components/SubmissionsByRoundListItem';


export default class SubmissionsByRoundList extends React.Component {
    renderListItems() {
        return this.props.items.map(v => {
            const submissions = v.submissions.map(v => {
               return <SubmissionsByRoundListItem key={`submission-${v.id}`} title={v.title} />;
            });
            return (
                <>
                    <SubmissionsByRoundListHeading key="status-{v.title}" title={v.title} count={v.submissions.length} />
                    <ul>
                        {submissions}
                    </ul>
                </>
            );
        });
    }

    render() {
        return (
            <>
                <div className="submissions-grid__header">
                    <select>
                        <option>Option 1</option>
                        <option>Option 2</option>
                        <option>Option 3</option>
                    </select>
                </div>
                <ul className="submissions-grid__list">
                    {this.renderListItems()}
                </ul>
            </>
        );
    }
}
