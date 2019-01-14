import React from 'react';
import SubmissionsByRoundListHeading from '@components/SubmissionsByRoundListHeading';
import SubmissionsByRoundListItem from '@components/SubmissionsByRoundListItem';

import './SubmissionsByRoundList.scss';

export default class SubmissionsByRoundList extends React.Component {
    renderListItems() {
        const listItems = [];
        for (const item of this.props.items) {
            listItems.push(
                <SubmissionsByRoundListHeading key={`status-${item.id}`} title={item.title} count={item.submissions.length} />
            );

            const submissions = [];
            for (const submission of item.submissions) {

                submissions.push(
                    <SubmissionsByRoundListItem key={`submission-${submission.id}`} title={submission.title} />
                );
            }

            listItems.push(
                <ul key={`submissions-list-${item.id}`}>
                    {submissions}
                </ul>
            );
        }
        return listItems;
    }

    render() {
        return (
            <div className="listing">
                <div className="listing__header">
                <form className="form form__select">
                    <select>
                        <option>Option 1</option>
                        <option>Option 2</option>
                        <option>Option 3</option>
                    </select>
                </form>
                </div>
                <ul className="listing__list">
                    {this.renderListItems()}
                </ul>
            </div>
        );
    }
}
