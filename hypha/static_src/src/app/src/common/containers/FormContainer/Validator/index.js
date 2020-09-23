
import validate from 'validate.js';


export default class Validator {
    constructor(values, constraints){
        this.values = values;
        this.constraints = constraints;
        this.errors = {}
        this.updateComparators()
    }

    updateComparators() {
        for (const field_name in this.constraints) {
            if (this.constraints[field_name] && this.constraints[field_name].equality) {
                const comparator = this.constraints[field_name].equality.comparator;
                this.constraints = this.constraints.setIn([field_name, 'equality', 'comparator'], new Function(comparator[0], comparator[1], comparator[2]));
            }
        }
    }

    validate() {
        this.errors = validate(this.values, this.constraints);
        return this.errors;
    }

    validateSingle(field_name) {
        const errors = this.validate();
        return errors && errors[field_name] ? {
            [field_name]: errors[field_name]
        } : false;
    }
    
}
