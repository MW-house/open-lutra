/** Auto-reset Zustand stores between tests.
 *
 * With vi.mock("zustand"), every store is reset to its initial state for each test.
 * Reference: https://zustand.docs.pmnd.rs/guides/testing
 */

import { afterEach } from "vitest";
import * as zustand from "zustand";

const storeResetFns = new Set<() => void>();

const createUncurried = <T>(stateCreator: zustand.StateCreator<T>) => {
  const store = (zustand.createStore as typeof zustand.createStore)(stateCreator);
  const initialState = store.getInitialState();
  storeResetFns.add(() => store.setState(initialState, true));
  return store;
};

export const create = (<T>(stateCreator: zustand.StateCreator<T>) => {
  return typeof stateCreator === "function" ? createUncurried(stateCreator) : createUncurried;
}) as typeof zustand.create;

afterEach(() => {
  for (const fn of storeResetFns) fn();
});
