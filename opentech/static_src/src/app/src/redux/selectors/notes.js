import { createSelector } from 'reselect';

import { getCurrentSubmission } from '@selectors/submissions';

const getNotes = state => state.notes.byID;

export const getNotesFetchState = state => state.notes.isFetching === true;

export const getNotesErrorState = state => state.notes.isErrored === true;

export const getNotesForCurrentSubmission = createSelector(
    [getCurrentSubmission, getNotes],
    (submission, notes) => {
        if (
            submission === undefined || submission === null ||
            submission.comments === null || submission.comments === undefined
        ) {
            return [];
        }
        return submission.comments.map(commentID => notes[commentID])
                           .filter(v => v !== undefined && v !== null)
    }
);

