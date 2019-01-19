import React from 'react';

import Download from 'images/download.svg';
import File from 'images/file.svg';

const ListAnswer = ({Wrapper, answers}) => (
    <ul>{
        answers.map((answer, index) => <li key={index}><Wrapper answer={answer} /></li>)
    }</ul>
);

const BasicAnswer = ({answer}) => <p>{ answer }</p>;

const BasicListAnswer = ({answer}) => <ListAnswer Wrapper={BasicAnswer} answers={answer} />;

const RichTextAnswer = ({answer}) => <div dangerouslySetInnerHTML={{ __html: answer }} />;

const FileAnswer = ({answer}) => (
    <a className="link link--download" href={answer.url}>
        <div>
            <File /><span>{answer.filename}</span>
        </div>
        <Download />
    </a>
);

const MultiFileAnswer = ({answer}) => <ListAnswer Wrapper={FileAnswer} answers={answer} />;

const AddressAnswer = ({answer}) => (
        <div>{
            Object.entries(answer)
                .filter(([key, value]) => !!value )
                .map(([key, value]) => <p>{value}</p> )}</div>
)


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

const Answer = ({ answer, type }) => {
    const AnswerType = answerTypes[type];

    if (!AnswerType) {return <>{type}</>}

    console.log(type)
    console.log(answer)

    return <AnswerType answer={answer} />;
}

export default Answer;
