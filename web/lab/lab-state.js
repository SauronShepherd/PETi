const initial = () => ({
  route: "COMMAND",
  selectedRunId: null,
  loading: {},
  errors: {},
  data: null,
  demo: false,
  pollingPaused: false,
});

let state = initial();
const listeners = new Set();

export const getState = () => state;
export function setState(patch) {
  state = {...state, ...patch};
  listeners.forEach((listener) => listener(state));
  return state;
}
export function subscribe(listener) {
  listeners.add(listener);
  return () => listeners.delete(listener);
}
export function reset() {
  state = initial();
  listeners.forEach((listener) => listener(state));
}
