import { useState } from 'react';
import { useDispatch } from 'react-redux';
import { setProfile } from '../store/user/actions';
import { API_BASE_URL } from '../utils/constants/api-constant';
import { transformAstrologyResponse } from '../utils/astrology-utils';

const initialFormData = {
  name: "",
  dateOfBirth: "",
  timeOfBirth: "",
  latitude: "",
  longitude: "",
  sixDegreeCorrection: false,
};

export const useAstrologyForm = () => {
  const dispatch = useDispatch();
  const [formData, setFormData] = useState(initialFormData);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const [moonDataForDashas, setMoonDataForDashas] = useState(null);
  const [chartDataForDashas, setChartDataForDashas] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      const dateObj = new Date(formData.dateOfBirth);
      const [hours, minutes] = formData.timeOfBirth.split(":");
      const year = dateObj.getFullYear();
      const month = dateObj.getMonth() + 1;
      const date = dateObj.getDate();

      const timezoneOffset = new Date().getTimezoneOffset();
      const timezone = -(timezoneOffset / 60);
      
      dispatch(setProfile({
        name: formData.name,
        dateOfBirth: formData.dateOfBirth,
        timeOfBirth: formData.timeOfBirth,
        latitude: formData.latitude,
        longitude: formData.longitude,
      }));

      const astrologyPayload = {
        year: year,
        month: month,
        date: date,
        hours: parseInt(hours, 10),
        minutes: parseInt(minutes, 10),
        seconds: 0,
        latitude: parseFloat(formData.latitude),
        longitude: parseFloat(formData.longitude),
        timezone: timezone,
        settings: {
          observation_point: "geocentric",
          ayanamsha: "lahiri",
        },
      };

      const apiKey = process.env.REACT_APP_ASTROLOGY_API_KEY;
      if (!apiKey) {
        throw new Error("ASTROLOGY_API_KEY environment variable is not set");
      }

      const astrologyResponse = await fetch(
        "https://json.freeastrologyapi.com/planets",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "x-api-key": apiKey,
          },
          body: JSON.stringify(astrologyPayload),
        }
      );

      if (!astrologyResponse.ok) {
        const errorData = await astrologyResponse.json().catch(() => ({}));
        throw new Error(
          errorData.message || `Astrology API error: ${astrologyResponse.status}`
        );
      }

      const astrologyData = await astrologyResponse.json();
      const transformedData = transformAstrologyResponse(
        astrologyData,
        formData.sixDegreeCorrection || false
      );

      const requiredFields = ['ascendant', 'sun', 'moon', 'mars', 'mercury', 'jupiter', 'venus', 'saturn', 'rahu', 'ketu'];
      const missingFields = requiredFields.filter(field => {
        const fieldData = transformedData[field];
        return !fieldData || !fieldData.degree || !fieldData.house;
      });

      if (missingFields.length > 0) {
        throw new Error(`Missing or invalid data for: ${missingFields.join(', ')}`);
      }

      const calculatePayload = { ...transformedData };
      const backendResponse = await fetch(
        `${API_BASE_URL}/api/calculate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(calculatePayload),
        }
      );

      const backendData = await backendResponse.json();
      if (!backendResponse.ok) {
        throw new Error(backendData.error || "Failed to calculate");
      }

      let dashaData = null;
      if (transformedData.moon && transformedData.moon.house && transformedData.moon.degree) {
        try {
          const { moon, ascendant, sun, mars, mercury, jupiter, venus, saturn, rahu, ketu } = transformedData;
          const chartData = { ascendant, sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu };
          const dashaPayload = {
            moon,
            birth_date: formData.dateOfBirth,
            chart_data: chartData
          };
          const dashaResponse = await fetch(
            `${API_BASE_URL}/api/dasha-info`,
            {
              method: "POST",
              headers: {
                "Content-Type": "application/json",
              },
              body: JSON.stringify(dashaPayload),
            }
          );

          if (dashaResponse.ok) {
            const dashaResponseData = await dashaResponse.json();
            if (dashaResponseData.status === 'success' && dashaResponseData.dasha) {
              dashaData = dashaResponseData.dasha;
            }
          }
        } catch (dashaErr) {
          console.warn("Failed to fetch dasha info:", dashaErr);
        }
      }

      const finalResults = {
        ...backendData,
        ...(dashaData && { dasha: dashaData })
      };
      setResults(finalResults);
      
      if (transformedData.moon) {
        setMoonDataForDashas(transformedData.moon);
        const { moon, ascendant, sun, mars, mercury, jupiter, venus, saturn, rahu, ketu } = transformedData;
        setChartDataForDashas({ ascendant, sun, moon, mars, mercury, jupiter, venus, saturn, rahu, ketu });
      }
    } catch (err) {
      setError(err.message || "An error occurred while calculating");
      console.error("Error:", err);
    } finally {
      setLoading(false);
    }
  };

  return {
    formData,
    setFormData,
    loading,
    results,
    error,
    moonDataForDashas,
    chartDataForDashas,
    handleSubmit,
  };
};
