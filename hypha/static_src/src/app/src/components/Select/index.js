import React from 'react'
import PropTypes from 'prop-types'

const Option = ({ value, display }) => {
    return <option value={value}>{display || value}</option>
}

Option.propTypes = {
    value: PropTypes.string.isRequired,
    display: PropTypes.string,
}

const Select = ({ options, onChange }) => {
    const items = [{ display: '---', value: '' }].concat(options)
    return (
        <select onChange={evt => onChange(evt.target.value)} >
            {items.map(({ value, display }) =>
                <Option key={value} value={value} display={display} />
            )}
        </select>
    )
}


Select.propTypes = {
    options: PropTypes.arrayOf(PropTypes.shape({
        value: PropTypes.string.isRequired,
        display: PropTypes.string,
    })),
    onChange: PropTypes.func,
}


export default Select
