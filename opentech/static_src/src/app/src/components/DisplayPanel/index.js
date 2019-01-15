import React from 'react';
import ApplicationDisplay from '@components/ApplicationDisplay'
import Tabber from '@components/Tabber'
import {Tab} from '@components/Tabber'
import './style.scss';

const DisplayPanel = () => {
    const data = {
        metaResponses: [{
            question: 'Requested Funding',
            answer: '123',
        },{
            question: 'Proposal Duration',
            answer: '1 month',
        },{
            question: 'Legal name',
            answer: 'Maya Summit'
        }],
        responses: [{
            question: 'Have you ever applied to or received funding as an OTF project?',
            answer: 'This is a string. Nisi officia ea exercitation anim fugiat ut nulla elit voluptate nostrud aliqua. Incididunt incididunt occaecat esse nostrud. Ad duis do cupidatat et voluptate amet sint sint velit deserunt.'
        },{
            question: 'Have you ever applied to or received funding as an OTF project?',
            answer: '<p>Yes</p><ul><li>one</li><li>two</li></ul>'
        }, {
            question: 'Have you ever applied to or received funding as an OTF project?',
            answer: ['One', 'Two', 'Three', 'Four', 'Five']
        }, {
            question: 'Have you ever applied to or received funding as an OTF project?',
            answer: ['<p>One</p>', '<p><b>Two</b></p>', '<p>Three</p>']
        }]
    }

    return (
        <Tabber className="display-panel">
            <Tab name="Application">
                <ApplicationDisplay submissionData={data} />
            </Tab>
            <Tab name="Notes">
                <p>Notes</p>
            </Tab>
            <Tab name="Status">
                <p>Status</p>
            </Tab>
        </Tabber>
    )
};

export default DisplayPanel;
