import {formInitialState} from './models';

export const initializer = (fields, initialValues = false) => {
    let formState = formInitialState
    for(const field of fields) {
        formState = formState.merge(
            {
                values: {
                  [field.kwargs.label]: field.kwargs.initial !== undefined ? field.kwargs.initial : ""
                },
                constraints: {
                  [field.kwargs.label]: getConstraints(field) 
                }
            },
            {deep: true}
        )
    }

    if (initialValues) {
      formState = formState.merge({values: {}},{ deep: true });
      for (const fieldId in initialValues) {
        const field = fields.find(field => field.id === fieldId);
        if(field) {
          formState = formState.merge({ values: {
            [field.kwargs.label]: initialValues[fieldId]
          } }, { deep: true });
        }
      }
    }

    // Add default values for dropdown
  for (const field of fields) {
    if (field.type === "ChoiceField" && !formState.values[field.kwargs.label]) {
      formState = formState.merge(
        {
          values: {
            [field.kwargs.label]: field.kwargs.choices[0][0]
          },
        },
        { deep: true }
      )
    }
  }    

    return formState;
};


const getConstraints = field => {
  let constraints = {}
  if (field.kwargs && field.kwargs.required) {
    constraints["presence"] = { allowEmpty: false }
  }

  if (field.kwargs && field.kwargs.max_length) {
    constraints["length"] = { maximum: true }
  }

  if (field.type === "EmailField") {
    constraints["email"] = true
  }

  if (field.type === "URLField") {
    constraints["url"] = true
  }

  if (field.kwargs && field.kwargs.min_length) {
    if (!constraints["length"]) {
      constraints["length"] = { minimum: true }
    } else {
      constraints["length"]["minimum"] =  true 
    }
  }

  if(field.type === "ScoredAnswerField"){
    constraints["type"] = "array"
  }
  return constraints
} 


export const parseValues = (fields, values) => {
  const formattedValues = {}
  for (const field of fields) {
    formattedValues[field.id] = values[field.kwargs.label]
  }
  return formattedValues
}