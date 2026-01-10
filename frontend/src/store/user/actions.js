import { SET_PROFILE, SET_SIX_DEGREE_CORRECTION, SET_MOON_DATA_FOR_DASHAS, SET_RESULTS } from "./reducer";


export const setProfile = (profile) => {
  return {
    type: SET_PROFILE,
    payload: { profile },
  };
};
export const setSixDegreeCorrection =  (sixDegreeCorrection) => {
  return {
    type: SET_SIX_DEGREE_CORRECTION,
    payload: { sixDegreeCorrection },
  };
};

export const setMoonDataForDashas = (moonDataForDashas) => {
  return {
    type: SET_MOON_DATA_FOR_DASHAS,
    payload: { moonDataForDashas },
  };
};

export const setResults = (results) => {
  return {
    type: SET_RESULTS,
    payload: { results },
  };
};