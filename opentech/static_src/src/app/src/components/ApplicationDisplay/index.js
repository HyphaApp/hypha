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
    console.log(question, answer);
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

        if (answer === true || answer === false) {
            return <div>{answer ? 'Yes' : 'No'}</div>;
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
        if (this.props.isLoading || this.props.submission === undefined) {
            return <div>Loading...</div>;
        } else if (this.props.isError) {
            return <div>Error occured...</div>;
        }
        const { meta_questions = [], questions = [] } = this.props.submission;

        return (
            <div>
                <h3>Proposal Information</h3>

                <div className="grid grid--proposal-info">
                    {meta_questions.map((response, index) => (
                        <Meta key={index} question={response.question} answer={response.answer} />
                    ))}
                </div>

                <div className="rich-text rich-text--answers">
                    {questions.map((response, index) => (
                        <Response key={index} question={response.question} answer={response.answer} />
                    ))}
                </div>
            </div>
        )
    }
}
