import { SIGN_MAP, PLANET_SYMBOLS } from "./constants";
import { capitalizeFirstLetter } from "./basic-logic";

export const getRasiName = (signNumber) => {
  return SIGN_MAP[signNumber] || "";
};

export const getPreviousSign = (signNumber) => {
  if (signNumber <= 1) {
    return 12;
  }
  return signNumber - 1;
};

export const transformAstrologyResponse = (apiResponse, applyCorrection = false) => {
  const planetData =
    apiResponse.output && apiResponse.output[1] ? apiResponse.output[1] : {};

  const transformed = {};
  const correction = applyCorrection ? 6 : 0;

  if (planetData.Ascendant) {
    const asc = planetData.Ascendant;
    const normDegree = parseFloat(asc.normDegree);
    const currentSign = asc.current_sign;
    
    if (!isNaN(normDegree) && typeof currentSign === 'number' && currentSign >= 1 && currentSign <= 12) {
      let correctedDegree = normDegree - correction;
      let correctedSign = currentSign;

      if (correctedDegree < 0) {
        correctedSign = getPreviousSign(asc.current_sign);
        correctedDegree = 30 + correctedDegree;
      }

      transformed.ascendant = {
        degree: Math.max(0, Math.min(30, correctedDegree)).toString(),
        house: getRasiName(correctedSign),
      };
    }
  }

  Object.keys(PLANET_SYMBOLS).forEach((apiName) => {
    const backendName = capitalizeFirstLetter(apiName.toLowerCase());
    if (planetData[backendName]) {
      const planet = planetData[backendName];
      const normDegree = parseFloat(planet.normDegree);
      const currentSign = planet.current_sign;
      
      if (!isNaN(normDegree) && typeof currentSign === 'number' && currentSign >= 1 && currentSign <= 12) {
        let correctedDegree = normDegree - correction;
        let correctedSign = currentSign;

        if (correctedDegree < 0) {
          correctedSign = getPreviousSign(currentSign);
          correctedDegree = 30 + correctedDegree;
        }

        transformed[apiName.toLowerCase()] = {
          degree: correctedDegree.toString(),
          house: getRasiName(correctedSign),
        };
      }
    }
  });

  return transformed;
};
