import React, {Component} from 'react';

import './styles.scss'

const Meta = ({ question, answer }) => {
    return (
        <div>
            <h5>{question}</h5>
            <p>{answer}</p>
        </div>
    )
}

const Response = ({question, answer}) => {
    return (
        <section>
            <h4>{question}</h4>
            <p>{answer}</p>
        </section>
    )
}

export default class ApplicationDisplay extends Component {
    render() {
        const { metaResponses, responses } = this.props.submissionData;

        return (
            <div className="application-display">
                <h3>Proposal Information</h3>

                <div className="grid grid--proposal-info">
                    {metaResponses.map(response => (
                        <Meta question={response.question} answer={response.answer} />
                    ))}
                </div>

                <div className="rich-text rich-text--answers">
                {responses.map(response => (
                    <Response question={response.question} answer={response.answer} />
                    ))}
                </div>
            </div>
        )
    }
}
