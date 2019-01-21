import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Answer, { answerPropTypes } from './answers'
import './styles.scss'


const MetaResponse = ({ question, answer, type }) => {
    return (
        <div>
            <h5>{question}</h5>
            <Answer type={type} answer={answer} />
        </div>
    )
}
MetaResponse.propTypes = {
    question: PropTypes.string.isRequired,
    answer: answerPropTypes,
    type: PropTypes.string.isRequired,
}


const Response = ({question, answer, type}) => {
    return (
        <section>
            <h4>{question}</h4>
            <Answer type={type} answer={answer} />
        </section>
    )
}
Response.propTypes = {
    question: PropTypes.string.isRequired,
    answer: answerPropTypes,
    type: PropTypes.string.isRequired,
}


export default class SubmissionDisplay extends Component {
    static propTypes = {
        isLoading: PropTypes.bool,
        isError: PropTypes.bool,
        submission: PropTypes.object,
    }

    render() {
        if (this.props.isLoading) {
            return <div>Loading...</div>;
        } else if (this.props.isError) {
            return <div>Error occured...</div>;
        } else if (this.props.submission === undefined) {
            return <div>Not selected</div>;
        }
        const { meta_questions = [], questions = [], stage} = this.props.submission;

        return (
            <div className="application-display">
                <h3>{stage} Information</h3>

                <div className="grid grid--proposal-info">
                    {meta_questions.map((response, index) => (
                        <MetaResponse key={index} {...response} />
                    ))}
                </div>

                <div className="rich-text rich-text--answers">
                    {questions.map((response, index) => (
                        <Response key={index} {...response} />
                    ))}
                </div>
            </div>
        )
    }
}
