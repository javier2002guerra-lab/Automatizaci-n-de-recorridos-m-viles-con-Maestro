import { useEffect } from 'react';
import { FlatList, Pressable, StyleSheet, Text, View } from 'react-native';
import { colores, sombra } from '../theme';
import type { Tarea } from '../types';

interface Props {
  tareas: Tarea[];
  cargando: boolean;
  confirmacion: string | null;
  onCerrarConfirmacion: () => void;
  onNuevaTarea: () => void;
  onAlternarCompletada: (id: string) => void;
}

export default function ListaTareas({
  tareas,
  cargando,
  confirmacion,
  onCerrarConfirmacion,
  onNuevaTarea,
  onAlternarCompletada,
}: Props) {
  // La confirmación se oculta sola pasados unos segundos.
  useEffect(() => {
    if (!confirmacion) return;
    const t = setTimeout(onCerrarConfirmacion, 8000);
    return () => clearTimeout(t);
  }, [confirmacion, onCerrarConfirmacion]);

  const pendientes = tareas.filter((t) => !t.completada).length;
  const completadas = tareas.length - pendientes;

  return (
    <View style={styles.contenedor} testID="pantalla-principal">
      <View style={styles.encabezado}>
        <Text style={styles.marca}>TaskFlow Mobile</Text>
        <Text style={styles.titulo} testID="titulo-pantalla-principal">
          Mis tareas
        </Text>
        <Text style={styles.resumen} testID="resumen-tareas">
          {`${pendientes} ${pendientes === 1 ? 'pendiente' : 'pendientes'} · ${completadas} ${
            completadas === 1 ? 'completada' : 'completadas'
          }`}
        </Text>
      </View>

      {confirmacion && (
        <View style={styles.banner} testID="mensaje-confirmacion" accessibilityLiveRegion="polite">
          <Text style={styles.bannerIcono}>✓</Text>
          <Text style={styles.bannerTexto}>{confirmacion}</Text>
          <Pressable
            onPress={onCerrarConfirmacion}
            hitSlop={12}
            testID="btn-cerrar-confirmacion"
            accessibilityRole="button"
            accessibilityLabel="Cerrar mensaje"
          >
            <Text style={styles.bannerCerrar}>✕</Text>
          </Pressable>
        </View>
      )}

      {cargando ? (
        <Text style={styles.cargando} testID="cargando-tareas">
          Cargando tareas…
        </Text>
      ) : (
        <FlatList
          data={tareas}
          keyExtractor={(t) => t.id}
          contentContainerStyle={tareas.length === 0 ? styles.listaVaciaContenedor : styles.lista}
          testID="lista-tareas"
          ListEmptyComponent={
            <View style={styles.vacio} testID="lista-vacia">
              <Text style={styles.vacioIcono}>📋</Text>
              <Text style={styles.vacioTitulo}>Aún no tienes tareas</Text>
              <Text style={styles.vacioTexto}>Pulsa “Nueva tarea” para registrar la primera.</Text>
            </View>
          }
          renderItem={({ item }) => (
            <View
              style={[styles.tarjeta, item.completada && styles.tarjetaCompletada]}
              testID={`tarea-${item.titulo}`}
            >
              <Pressable
                onPress={() => onAlternarCompletada(item.id)}
                style={[styles.check, item.completada && styles.checkActivo]}
                hitSlop={8}
                testID={`check-${item.titulo}`}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: item.completada }}
                accessibilityLabel={`Marcar como completada: ${item.titulo}`}
              >
                {item.completada && <Text style={styles.checkMarca}>✓</Text>}
              </Pressable>
              <View style={styles.tarjetaCuerpo}>
                <Text
                  style={[styles.tarjetaTitulo, item.completada && styles.tachado]}
                  testID={`titulo-${item.titulo}`}
                >
                  {item.titulo}
                </Text>
                {item.descripcion ? (
                  <Text style={styles.tarjetaDescripcion} numberOfLines={2}>
                    {item.descripcion}
                  </Text>
                ) : null}
                <Text
                  style={[styles.estado, item.completada ? styles.estadoCompletada : styles.estadoPendiente]}
                  testID={`estado-${item.titulo}`}
                >
                  {item.completada ? 'Completada' : 'Pendiente'}
                </Text>
              </View>
            </View>
          )}
        />
      )}

      <Pressable
        style={({ pressed }) => [styles.botonFlotante, pressed && { backgroundColor: colores.primarioOscuro }]}
        onPress={onNuevaTarea}
        testID="btn-nueva-tarea"
        accessibilityRole="button"
        accessibilityLabel="Nueva tarea"
      >
        <Text style={styles.botonFlotanteTexto}>＋ Nueva tarea</Text>
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  encabezado: {
    backgroundColor: colores.primario,
    paddingHorizontal: 20,
    paddingTop: 20,
    paddingBottom: 24,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  marca: { color: '#C7D2FE', fontSize: 13, fontWeight: '600', letterSpacing: 1, textTransform: 'uppercase' },
  titulo: { color: '#FFFFFF', fontSize: 28, fontWeight: '700', marginTop: 4 },
  resumen: { color: '#E0E7FF', fontSize: 14, marginTop: 6 },
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colores.exitoSuave,
    borderColor: colores.exito,
    borderWidth: 1,
    borderRadius: 12,
    marginHorizontal: 16,
    marginTop: 16,
    paddingVertical: 12,
    paddingHorizontal: 14,
  },
  bannerIcono: { color: colores.exito, fontSize: 18, fontWeight: '700', marginRight: 10 },
  bannerTexto: { flex: 1, color: '#065F46', fontSize: 15, fontWeight: '600' },
  bannerCerrar: { color: '#065F46', fontSize: 16, paddingLeft: 8 },
  cargando: { textAlign: 'center', marginTop: 40, color: colores.textoSecundario },
  lista: { padding: 16, paddingBottom: 110 },
  listaVaciaContenedor: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  vacio: { alignItems: 'center' },
  vacioIcono: { fontSize: 48, marginBottom: 12 },
  vacioTitulo: { fontSize: 18, fontWeight: '700', color: colores.texto },
  vacioTexto: { fontSize: 14, color: colores.textoSecundario, marginTop: 6, textAlign: 'center' },
  tarjeta: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: colores.superficie,
    borderRadius: 14,
    padding: 14,
    marginBottom: 12,
    ...sombra,
  },
  tarjetaCompletada: { backgroundColor: '#F9FAFB' },
  check: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: colores.primario,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
    marginTop: 2,
  },
  checkActivo: { backgroundColor: colores.exito, borderColor: colores.exito },
  checkMarca: { color: '#FFFFFF', fontWeight: '800', fontSize: 15 },
  tarjetaCuerpo: { flex: 1 },
  tarjetaTitulo: { fontSize: 16, fontWeight: '700', color: colores.texto },
  tachado: { textDecorationLine: 'line-through', color: colores.textoSecundario },
  tarjetaDescripcion: { fontSize: 14, color: colores.textoSecundario, marginTop: 4 },
  estado: {
    alignSelf: 'flex-start',
    marginTop: 8,
    fontSize: 12,
    fontWeight: '700',
    paddingHorizontal: 10,
    paddingVertical: 3,
    borderRadius: 999,
    overflow: 'hidden',
  },
  estadoPendiente: { backgroundColor: colores.pendienteSuave, color: colores.pendiente },
  estadoCompletada: { backgroundColor: colores.exitoSuave, color: colores.exito },
  botonFlotante: {
    position: 'absolute',
    right: 20,
    bottom: 24,
    backgroundColor: colores.primario,
    borderRadius: 28,
    paddingHorizontal: 22,
    paddingVertical: 16,
    ...sombra,
    elevation: 6,
  },
  botonFlotanteTexto: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
});
