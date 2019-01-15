import React, {Component} from 'react';

import './styles.scss'

const Meta = ({ question, answer }) => {
    return (
        <div>
            <h5>{question}</h5>
            <p dangerouslySetInnerHTML={{ __html: answer }} />
        </div>
    )
}

const Response = ({question, answer}) => {
    // array that doesn't contain HTML
    if (Array.isArray(answer) && !answer[0].startsWith('<')) {
        return  (
            <section>
                <h4>{question}</h4>
                <ul>{answer.map((a) => <li key={a}>{a}</li>)}</ul>
            </section>
        )
    // array that contains HTML
    } else if (Array.isArray(answer)) {
        return (
            <section>
                <h4>{question}</h4>
                {answer.map(a => <div dangerouslySetInnerHTML={{ __html: a }} />)}
            </section>
        )
    }

    // strings with and without HTML
    return (
        <section>
            <h4>{question}</h4>
            <p dangerouslySetInnerHTML={{ __html: answer }} />
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
