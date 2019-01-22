import moment from 'moment';
import 'moment-timezone';

// Use GMT globally for all the dates.
moment.tz.setDefault('GMT');

// Use en-US locale for all the dates.
moment.locale('en');
