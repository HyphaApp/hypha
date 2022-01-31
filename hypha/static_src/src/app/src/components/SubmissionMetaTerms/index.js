import React from 'react';
import PropTypes from 'prop-types';
import SidebarBlock from '@components/SidebarBlock';
import './styles.scss';

const SubmissionMetaTerms = (props) => {

    if (!props.metaTerms.length) {
        return (
            <SidebarBlock title="Meta Terms">
                <p>No Meta Terms available.</p>
            </SidebarBlock>
        );
    }

    return (
        <SidebarBlock title="Meta Terms">
            <div className="submission-metaterms">
                {props.metaTerms.map(metaTerm => {
                    return (
                        <dl key={metaTerm.parentId}>
                            <dt key={metaTerm.parentId}>
                                <strong>{metaTerm.parent}</strong>
                            </dt>
                            {metaTerm.children.map(child => {
                                return <dd key={child.id}>{child.name}</dd>;
                            })}
                        </dl>
                    );
                })}
            </div>
        </SidebarBlock>
    );
};

SubmissionMetaTerms.propTypes = {
    metaTerms: PropTypes.array
};

export default SubmissionMetaTerms;
