import { DEFAULT_INPUT } from "./scenario";
import type { ScenarioInput } from "./types";

const KEY = "resqai.scenario";

export function saveScenarioInput(input: ScenarioInput) {
  if (typeof window === "undefined") return;
  window.sessionStorage.setItem(KEY, JSON.stringify(input));
}

export function loadScenarioInput(): ScenarioInput {
  if (typeof window === "undefined") return DEFAULT_INPUT;
  try {
    const raw = window.sessionStorage.getItem(KEY);
    if (!raw) return DEFAULT_INPUT;
    return { ...DEFAULT_INPUT, ...(JSON.parse(raw) as Partial<ScenarioInput>) };
  } catch {
    return DEFAULT_INPUT;
  }
}
