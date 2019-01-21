import React from 'react';
import PropTypes from 'prop-types';

import Download from 'images/download.svg';
import File from 'images/file.svg';

const answerType = {answer: PropTypes.string.isRequired}
const arrayAnswerType = {answer: PropTypes.arrayOf(PropTypes.string)}
const fileType = {answer: PropTypes.shape({
    filename: PropTypes.string.isRequired,
    url:PropTypes.string.isRequired,
})}

const ListAnswer = ({Wrapper, answers}) => (
    <ul>{
        answers.map((answer, index) => <li key={index}><Wrapper answer={answer} /></li>)
    }</ul>
);
ListAnswer.propTypes = {
    Wrapper: PropTypes.element,
    ...arrayAnswerType,
}

const BasicAnswer = ({answer}) => <p>{ answer }</p>;
BasicAnswer.propTypes = answerType

const BasicListAnswer = ({answer}) => <ListAnswer Wrapper={BasicAnswer} answers={answer} />;
BasicListAnswer.propTypes = arrayAnswerType

const RichTextAnswer = ({answer}) => <div dangerouslySetInnerHTML={{ __html: answer }} />;
RichTextAnswer.propTypes = answerType

const FileAnswer = ({answer}) => (
    <a className="link link--download" href={answer.url}>
        <div>
            <File /><span>{answer.filename}</span>
        </div>
        <Download />
    </a>
);
FileAnswer.propTypes = fileType

const MultiFileAnswer = ({answer}) => <ListAnswer Wrapper={FileAnswer} answers={answer} />;
MultiFileAnswer.propTypes = {answer: PropTypes.arrayOf(fileType)}

const AddressAnswer = ({answer}) => (
        <div>{
            Object.entries(answer)
                .filter(([key, value]) => !!value )
                  .map(([key, value]) => <p key={key}>{value}</p> )}
        </div>
)
AddressAnswer.propTypes = {answer: PropTypes.objectOf(PropTypes.string)}


const answerTypes = {
    'no_response': BasicAnswer,
    'char': BasicAnswer,
    'email': BasicAnswer,
    'name': BasicAnswer,
    'value': BasicAnswer,
    'title': BasicAnswer,
    'full_name': BasicAnswer,
    'duration': BasicAnswer,
    'date': BasicAnswer,
    'checkbox': BasicAnswer,
    'dropdown': BasicAnswer,
    'radios': BasicAnswer,

    // SPECIAL
    'rich_text': RichTextAnswer,
    'address': AddressAnswer,
    'category': BasicListAnswer,
    // Files
    'file': FileAnswer,
    'multi_file': MultiFileAnswer,
}

export const answerPropTypes = PropTypes.oneOfType([
    PropTypes.string,
    PropTypes.object,
    PropTypes.arrayOf(PropTypes.string),
    PropTypes.arrayOf(PropTypes.object),
])

const Answer = ({ answer, type }) => {
    const AnswerType = answerTypes[type];

    return <AnswerType answer={answer} />;
}
Answer.propTypes = {
    answer: answerPropTypes,
    type: PropTypes.string.isRequired,
}

export default Answer;
