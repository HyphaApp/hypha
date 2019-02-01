import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Answer, { answerPropTypes } from './answers'
import LoadingPanel from '@components/LoadingPanel';

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
            return (
                <div className="display-panel__loading">
                    <LoadingPanel />
                </div>
            )
        } else if (this.props.isError) {
            return (
                <div className="display-panel__loading">
                    <p>Something went wrong. Please try again later.</p>
                </div>
            )
        } else if (this.props.submission === undefined) {
            return (
                <div className="display-panel__loading">
                    <p>Please select a submission.</p>
                </div>
            )
        }
        const { metaQuestions = [], questions = [], stage} = this.props.submission;

        return (
            <div className="application-display">
                <h3>{stage} Information</h3>

                <div className="grid grid--proposal-info">
                    {metaQuestions.map((response, index) => (
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
