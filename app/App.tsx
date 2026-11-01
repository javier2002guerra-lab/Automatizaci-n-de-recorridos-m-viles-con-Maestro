import { useCallback, useEffect, useState } from 'react';
import { BackHandler, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import ListaTareas from './src/screens/ListaTareas';
import NuevaTarea from './src/screens/NuevaTarea';
import { cargarTareas, crearId, guardarTareas } from './src/storage';
import { colores } from './src/theme';
import type { Pantalla, Tarea } from './src/types';

export const MENSAJE_GUARDADO = 'Tarea guardada correctamente';

export default function App() {
  const [pantalla, setPantalla] = useState<Pantalla>('lista');
  const [tareas, setTareas] = useState<Tarea[]>([]);
  const [cargando, setCargando] = useState(true);
  const [confirmacion, setConfirmacion] = useState<string | null>(null);

  // Al abrir la app se recuperan las tareas guardadas en el almacenamiento local.
  useEffect(() => {
    cargarTareas()
      .then(setTareas)
      .finally(() => setCargando(false));
  }, []);

  // Botón "atrás" de Android: desde el formulario vuelve al listado.
  useEffect(() => {
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (pantalla === 'nueva') {
        setPantalla('lista');
        return true;
      }
      return false;
    });
    return () => sub.remove();
  }, [pantalla]);

  const actualizar = useCallback(async (nuevas: Tarea[]) => {
    setTareas(nuevas);
    await guardarTareas(nuevas);
  }, []);

  const agregarTarea = async (titulo: string, descripcion: string) => {
    const tarea: Tarea = {
      id: crearId(),
      titulo,
      descripcion,
      completada: false,
      creadaEn: new Date().toISOString(),
    };
    await actualizar([tarea, ...tareas]);
    setConfirmacion(MENSAJE_GUARDADO);
    setPantalla('lista');
  };

  const alternarCompletada = (id: string) => {
    actualizar(tareas.map((t) => (t.id === id ? { ...t, completada: !t.completada } : t)));
  };

  const cerrarConfirmacion = useCallback(() => setConfirmacion(null), []);

  return (
    <SafeAreaProvider>
      <SafeAreaView style={styles.raiz} edges={['top', 'bottom']}>
        <StatusBar style="light" />
        {pantalla === 'lista' ? (
          <ListaTareas
            tareas={tareas}
            cargando={cargando}
            confirmacion={confirmacion}
            onCerrarConfirmacion={cerrarConfirmacion}
            onNuevaTarea={() => {
              setConfirmacion(null);
              setPantalla('nueva');
            }}
            onAlternarCompletada={alternarCompletada}
          />
        ) : (
          <NuevaTarea onGuardar={agregarTarea} onCancelar={() => setPantalla('lista')} />
        )}
      </SafeAreaView>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  raiz: { flex: 1, backgroundColor: colores.primario },
});
