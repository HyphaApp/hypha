import React from 'react'
import PropTypes from 'prop-types'
import SidebarBlock from '@components/SidebarBlock'
import './styles.scss'

const SubmissionMetaTerms = (props) => {
    return (
        <SidebarBlock title="Meta Terms">
            <div className="submission-metaterms">
                {props.metaTerms.length != 0 
                ?
                    props.metaTerms.map(metaTerm => {
                        return(
                            <dl key={metaTerm.parentId}>
                                <dt key={metaTerm.parentId}>
                                    <strong>{metaTerm.parent}</strong>
                                </dt>
                                {metaTerm.children.map(child => {
                                    return <dd key={child.id}>{child.name}</dd>
                                })}
                            </dl>
                        )
                    })
                : 
                <p>None. Meta terms can be added to a submission using Meta terms button at top.</p>}
            </div>
        </SidebarBlock>
    )
}

SubmissionMetaTerms.propTypes = {
    metaTerms: PropTypes.array,
}

export default SubmissionMetaTerms;
