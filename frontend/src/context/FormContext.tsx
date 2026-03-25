"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface FormState {
  fileId: string | null;
  filename: string | null;
  fields: string[];
  fieldCount: number;
  isAnalyzed: boolean;
}

interface FormCtx extends FormState {
  setForm: (s: Partial<FormState>) => void;
  reset: () => void;
}

const init: FormState = { fileId: null, filename: null, fields: [], fieldCount: 0, isAnalyzed: false };
const Ctx = createContext<FormCtx>({ ...init, setForm: () => {}, reset: () => {} });

export function FormProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<FormState>(init);
  const setForm = (s: Partial<FormState>) => setState((p) => ({ ...p, ...s }));
  const reset = () => setState(init);
  return <Ctx.Provider value={{ ...state, setForm, reset }}>{children}</Ctx.Provider>;
}

export const useForm = () => useContext(Ctx);
