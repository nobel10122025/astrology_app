export const SET_PROFILE = "SET_PROFILE";
export const SET_SIX_DEGREE_CORRECTION = "SET_SIX_DEGREE_CORRECTION";
export const SET_MOON_DATA_FOR_DASHAS = "SET_MOON_DATA_FOR_DASHAS";
export const SET_RESULTS = "SET_RESULTS";

const initialState = {
  profile: {
    name: "",
    dateOfBirth: "",
    timeOfBirth: "",
    latitude: "",
    longitude: "",
  },
  calculations: {
    sixDegreeCorrection: false,
    moonDataForDashas: null,
  }, 
  results: null,
};

const userReducer = (state = initialState, action) => {
  switch (action.type) {
    case SET_PROFILE:
      return {
        ...state,
        profile: {
          ...state.profile,
          ...action.payload.profile,
        }
      };
    case SET_SIX_DEGREE_CORRECTION:
      return {
        ...state,
        calculations: {
          ...state.calculations,
          sixDegreeCorrection: action.payload.sixDegreeCorrection,
        }
      };
    case SET_MOON_DATA_FOR_DASHAS:
      return {
        ...state,
        calculations: {
          ...state.calculations,
          moonDataForDashas: action.payload.moonDataForDashas,
        }
      };
    case SET_RESULTS:
      return {
        ...state,
        results: action.payload.results,
      };
    default:
      return state;
  }
};

export default userReducer;