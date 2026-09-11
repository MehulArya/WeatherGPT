import { useCallback, useEffect, useState } from "react";
import { listFavorites, addFavorite, removeFavorite, getClientKey } from "../api/favorites";

export function useFavorites() {
  const [status, setStatus] = useState("loading");
  const [favorites, setFavorites] = useState([]);
  const [error, setError] = useState(null);
  const clientKey = getClientKey();

  const load = useCallback(async () => {
    setStatus("loading");
    try {
      const data = await listFavorites(clientKey);
      setFavorites(data);
      setStatus("success");
    } catch (err) {
      setError(err);
      setStatus("error");
    }
  }, [clientKey]);

  useEffect(() => {
    load();
  }, [load]);

  const add = useCallback(
    async (loc) => {
      const optimistic = { id: `temp-${Date.now()}`, client_key: clientKey, ...loc };
      setFavorites((prev) => [...prev, optimistic]);
      try {
        const saved = await addFavorite({ client_key: clientKey, ...loc });
        setFavorites((prev) => prev.map((f) => (f.id === optimistic.id ? saved : f)));
      } catch (err) {
        setFavorites((prev) => prev.filter((f) => f.id !== optimistic.id));
        throw err;
      }
    },
    [clientKey]
  );

  const remove = useCallback(
    async (id) => {
      const prev = favorites;
      setFavorites((f) => f.filter((x) => x.id !== id));
      try {
        await removeFavorite(id, clientKey);
      } catch (err) {
        setFavorites(prev);
        throw err;
      }
    },
    [favorites, clientKey]
  );

  return { status, favorites, error, add, remove, reload: load };
}
