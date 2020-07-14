import {
  ExperimentReducerActionType,
  ExperimentData,
} from "experimenter-types/experiment";
import { ExperimentReducerAction } from "experimenter-types/experiment";

export const fetchExperiment = (experimentSlug: string) => async (
  experimentData: ExperimentData,
  dispatch: React.Dispatch<ExperimentReducerAction>,
): Promise<void> => {
  const response = await fetch(`/api/v3/experiments/${experimentSlug}/`, {
    method: "GET",
    headers: {
      "Content-Type": "application/json",
    },
  });

  const data = await response.json();
  dispatch({
    type: ExperimentReducerActionType.UPDATE_STATE,
    state: data,
  });
};

export const saveExperiment = async (
  experimentSlug: string,
  formData: ExperimentData,
): Promise<any> => {
  const url = experimentSlug
    ? `/api/v3/experiments/${experimentSlug}/`
    : "/api/v3/experiments/";
  return await fetch(url, {
    method: experimentSlug ? "PUT" : "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(formData),
  });
};

export const updateExperiment = (name: string, value: string | string[]) => (
  experimentData: ExperimentData,
  dispatch: React.Dispatch<ExperimentReducerAction>,
): void => {
  dispatch({
    type: ExperimentReducerActionType.UPDATE_STATE,
    state: {
      ...experimentData,
      [name]: value,
    },
  });
};
