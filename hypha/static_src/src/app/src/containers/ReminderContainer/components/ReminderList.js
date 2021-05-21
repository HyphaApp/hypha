import React from 'react';
import PropTypes from 'prop-types';
import DeleteIcon from '@material-ui/icons/Delete';
import Tooltip from '@material-ui/core/Tooltip';
import './style.scss'

class ReminderList extends React.PureComponent {

    render() {
        return (<ul>
            <li>
                <strong>{this.props.title}</strong>
                <ul>
                {this.props.reminders.map(reminder => {
                    return <li style={{color : reminder.is_expired ? 'grey' : 'black'}} className="list-item" key={reminder.id}> 
                                <div className="title-text">{reminder.title ? reminder.title : "untitled reminder"}</div> 
                                <Tooltip title={<span style={{fontSize: '14px'}}>Delete</span>} placement="right-start">
                                    <DeleteIcon 
                                    className="delete-icon"
                                    fontSize="small" 
                                    onClick={() => this.props.deleteReminder(this.props.submissionID, reminder.id)}
                                    />
                                </Tooltip>
                            </li>
                })}
                </ul>
            </li>
        </ul>)
    }
}

ReminderList.propTypes = {
    reminders: PropTypes.array,
    deleteReminder: PropTypes.func,
    submissionID: PropTypes.number,
    title: PropTypes.string
}

export default ReminderList;
