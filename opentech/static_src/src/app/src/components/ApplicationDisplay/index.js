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
    const containsHtml = (text) => {
        return text.startsWith('<');
    }

    const renderAnswer = () => {
        // handle arrays with and without html
        if (Array.isArray(answer)) {
            return <ul>
                {answer.map((a, i) => {
                    if (containsHtml(a)) {
                        return <li key={i} dangerouslySetInnerHTML={{ __html: a }} />
                    } else {
                        return <li key={i}>{a}</li>
                    }
                })}
            </ul>
        }

        // handle strings with and without html
        if (containsHtml(answer)) {
            return <div dangerouslySetInnerHTML={{ __html: answer }} />
        } else {
            return <div><p>{answer}</p></div>
        }
    }

    return (
        <section>
            <h4>{question}</h4>
            {renderAnswer()}
        </section>
    )
}

export default class ApplicationDisplay extends Component {
    render() {
        const { metaResponses, responses } = this.props.submissionData;

        return (
            <div>
                <h3>Proposal Information</h3>

                <div className="grid grid--proposal-info">
                    {metaResponses.map((response, index) => (
                        <Meta key={index} question={response.question} answer={response.answer} />
                    ))}
                </div>

                <div className="rich-text rich-text--answers">
                    {responses.map((response, index) => (
                        <Response key={index} question={response.question} answer={response.answer} />
                    ))}
                </div>
            </div>
        )
    }
}
