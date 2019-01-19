import React from 'react';

const ListAnswer = ({children}) =><ul>{children.map((child, index) => <li key={index}>{child}</li>)}</ul>;

const BasicAnswer = ({answer}) => <p>{ answer }</p>;

const RichTextAnswer = ({answer}) => <div dangerouslySetInnerHTML={{ __html: answer }} />;

const FileAnswer = ({answer}) => <a href={answer.url}>{answer.filename}</a>;

const MultiFileAnswer = ({answer}) => <ListAnswer>{answer.map(element => <FileAnswer answer={element} />)}</ListAnswer>

const answerTypes = {
    'no_response': BasicAnswer,
    'email': BasicAnswer,
    'name': BasicAnswer,
    'value': BasicAnswer,
    'title': BasicAnswer,
    'full_name': BasicAnswer,
    'duration': BasicAnswer,
    'address': null,
    'date': BasicAnswer,
    'rich_text': RichTextAnswer,
    'checkbox': BasicAnswer,
    'file': FileAnswer,
    'multi_file': MultiFileAnswer,
}

const Answer = ({ answer, type }) => {
    const AnswerType = answerTypes[type];

    if (!AnswerType) {return <>{type}</>}

    console.log(type)
    console.log(answer)

    return <AnswerType answer={answer} />;
}

export default Answer;
