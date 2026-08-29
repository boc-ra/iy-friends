import { useEffect, useState } from "react";

type State<T> = { loading: boolean; data: T | null; error: string | null };

// データ取得用の軽量フック。依存が変わると再取得する。
export function useAsync<T>(fn: () => Promise<T>, deps: unknown[]): State<T> {
  const [state, setState] = useState<State<T>>({ loading: true, data: null, error: null });

  useEffect(() => {
    let active = true;
    setState({ loading: true, data: null, error: null });
    fn()
      .then((data) => {
        if (active) setState({ loading: false, data, error: null });
      })
      .catch((e: unknown) => {
        const message = e instanceof Error ? e.message : "読み込みに失敗しました";
        if (active) setState({ loading: false, data: null, error: message });
      });
    return () => {
      active = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return state;
}
