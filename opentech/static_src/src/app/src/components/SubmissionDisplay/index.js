import React, {Component} from 'react';
import PropTypes from 'prop-types';

import Answer, { answerPropTypes } from './answers'
import LoadingPanel from '@components/LoadingPanel';
import InlineLoading from '@components/InlineLoading';

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
        const { metaQuestions = [], questions = [], stage } = this.props.submission || {};

        if (this.props.isError) {
            return (
                <div className="display-panel__loading">
                    <p>Something went wrong. Please try again later.</p>
                </div>
            )
        } else if (this.props.submission === undefined && !this.props.isLoading) {
            return (
                <div className="display-panel__loading">
                    <p>Please select a submission.</p>
                </div>
            )
        }

        if (questions.length == 0) {
            return (
                <div className="display-panel__loading">
                    <LoadingPanel />
                </div>
            )
        }

        return (
            <div className="application-display">
                    {this.props.isLoading &&
                        <InlineLoading />
                    }

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
