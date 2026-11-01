import AsyncStorage from '@react-native-async-storage/async-storage';
import type { Tarea } from './types';

// Clave única donde se guarda el listado completo en el almacenamiento local del dispositivo.
// No hay backend: los datos viven solo en el almacenamiento privado de la app.
const CLAVE_TAREAS = '@taskflow/tareas';

export async function cargarTareas(): Promise<Tarea[]> {
  const json = await AsyncStorage.getItem(CLAVE_TAREAS);
  if (!json) return [];
  try {
    const datos = JSON.parse(json);
    return Array.isArray(datos) ? (datos as Tarea[]) : [];
  } catch {
    return [];
  }
}

export async function guardarTareas(tareas: Tarea[]): Promise<void> {
  await AsyncStorage.setItem(CLAVE_TAREAS, JSON.stringify(tareas));
}

export function crearId(): string {
  return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 8)}`;
}
