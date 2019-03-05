import React from 'react';
import PropTypes from 'prop-types';
import { connect } from 'react-redux'

import GroupedListing from '@components/GroupedListing';
import {
    loadCurrentRound,
    loadCurrentRoundSubmissions,
    setCurrentSubmission,
} from '@actions/submissions';
import {
    getCurrentRoundSubmissions,
    getCurrentSubmissionID,
    getSubmissionsByRoundError,
} from '@selectors/submissions';
import {
    getCurrentRound,
    getCurrentRoundID,
} from '@selectors/rounds';


const loadData = props => {
    props.loadRound(['workflow'])
    props.loadSubmissions()
}

class ByStatusListing extends React.Component {
    static propTypes = {
        loadRound: PropTypes.func.isRequired,
        loadSubmissions: PropTypes.func.isRequired,
        submissions: PropTypes.arrayOf(PropTypes.object),
        roundID: PropTypes.number,
        round: PropTypes.object,
        errorMessage: PropTypes.string,
        setCurrentItem: PropTypes.func,
        activeSubmission: PropTypes.number,
        shouldSelectFirst: PropTypes.bool,
    };

    componentDidMount() {
        // Update items if round ID is defined.
        if ( this.props.roundID ) {
            loadData(this.props)
        }
    }

    componentDidUpdate(prevProps) {
        const { roundID } = this.props;
        // Update entries if round ID is changed or is not null.
        if (roundID && prevProps.roundID !== roundID) {
            loadData(this.props)
        }
    }

    prepareOrder(round) {
        if ( !round ) { return []}
        const slugify = value => value.toLowerCase().replace(/\s/g, '-')
        const workflow = round.workflow
        const order = workflow.reduce((accumulator, {display, value}, idx) => {
            const key = slugify(display);
            const existing = accumulator[key] || {}
            const existingValues = existing.values || []
            const position = existing.position || idx
            accumulator[key] = {key, display, position, values: [...existingValues, value]}
            return accumulator
        }, {})
        const arrayOrder = Object.values(order).sort((a,b) => a.position - b.position)
        return arrayOrder
    }

    render() {
        const { errorMessage, submissions, round, setCurrentItem, activeSubmission, shouldSelectFirst } = this.props;
        const isLoading = !round || ( round && (round.isFetching || round.submissions.isFetching) )
        const order = this.prepareOrder(round)
        return <GroupedListing
                    isLoading={isLoading}
                    errorMessage={errorMessage}
                    items={submissions}
                    activeItem={activeSubmission}
                    onItemSelection={setCurrentItem}
                    shouldSelectFirst={shouldSelectFirst}
                    groupBy={'status'}
                    order={ order } />;
    }
}

const mapStateToProps = state => ({
    roundID: getCurrentRoundID(state),
    submissions: getCurrentRoundSubmissions(state),
    round: getCurrentRound(state),
    errorMessage: getSubmissionsByRoundError(state),
    activeSubmission: getCurrentSubmissionID(state),
})

const mapDispatchToProps = dispatch => ({
    loadRound: fields => dispatch(loadCurrentRound(fields)),
    loadSubmissions: () => dispatch(loadCurrentRoundSubmissions()),
    setCurrentItem: id => dispatch(setCurrentSubmission(id)),
});

export default connect(
    mapStateToProps,
    mapDispatchToProps
)(ByStatusListing);
