import { type ComponentRef, useRef, useState } from 'react';
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native';
import { colores, sombra } from '../theme';

export const MENSAJE_TITULO_OBLIGATORIO = 'El título es obligatorio';
const LONGITUD_MAXIMA_TITULO = 80;

interface Props {
  onGuardar: (titulo: string, descripcion: string) => Promise<void>;
  onCancelar: () => void;
}

export default function NuevaTarea({ onGuardar, onCancelar }: Props) {
  const [titulo, setTitulo] = useState('');
  const [descripcion, setDescripcion] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [guardando, setGuardando] = useState(false);
  const refDescripcion = useRef<ComponentRef<typeof TextInput>>(null);

  const guardar = async () => {
    if (guardando) return;
    const tituloLimpio = titulo.trim();
    if (!tituloLimpio) {
      // Validación: no se crea ningún registro si el título está vacío o solo tiene espacios.
      setError(MENSAJE_TITULO_OBLIGATORIO);
      return;
    }
    setError(null);
    setGuardando(true);
    try {
      await onGuardar(tituloLimpio, descripcion.trim());
    } finally {
      setGuardando(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.contenedor}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      testID="pantalla-formulario"
    >
      <View style={styles.encabezado}>
        <Pressable
          onPress={onCancelar}
          hitSlop={12}
          testID="btn-volver"
          accessibilityRole="button"
          accessibilityLabel="Volver"
        >
          <Text style={styles.volver}>← Volver</Text>
        </Pressable>
        <Text style={styles.titulo} testID="titulo-formulario">
          Nueva tarea
        </Text>
        <Text style={styles.subtitulo}>Completa los datos y pulsa “Guardar tarea”.</Text>
      </View>

      <ScrollView contentContainerStyle={styles.formulario} keyboardShouldPersistTaps="handled">
        <View style={styles.tarjeta}>
          <Text style={styles.etiqueta}>
            Título <Text style={styles.obligatorio}>*</Text>
          </Text>
          <TextInput
            style={[styles.campo, error && styles.campoError]}
            value={titulo}
            onChangeText={(v) => {
              setTitulo(v);
              if (error && v.trim()) setError(null);
            }}
            placeholder="Ej.: Preparar la presentación"
            placeholderTextColor="#9CA3AF"
            maxLength={LONGITUD_MAXIMA_TITULO}
            returnKeyType="next"
            submitBehavior="submit"
            onSubmitEditing={() => refDescripcion.current?.focus()}
            testID="input-titulo"
            accessibilityLabel="Título de la tarea"
          />
          {error ? (
            <Text style={styles.textoError} testID="error-titulo" accessibilityLiveRegion="assertive">
              {error}
            </Text>
          ) : (
            <Text style={styles.ayuda}>Campo obligatorio · máximo {LONGITUD_MAXIMA_TITULO} caracteres</Text>
          )}

          <Text style={[styles.etiqueta, { marginTop: 18 }]}>Descripción (opcional)</Text>
          <TextInput
            ref={refDescripcion}
            style={[styles.campo, styles.campoMultilinea]}
            value={descripcion}
            onChangeText={setDescripcion}
            placeholder="Detalles de la tarea"
            placeholderTextColor="#9CA3AF"
            multiline
            textAlignVertical="top"
            testID="input-descripcion"
            accessibilityLabel="Descripción de la tarea"
          />
        </View>

        <Pressable
          style={({ pressed }) => [styles.botonGuardar, (pressed || guardando) && { opacity: 0.85 }]}
          onPress={guardar}
          disabled={guardando}
          testID="btn-guardar"
          accessibilityRole="button"
          accessibilityLabel="Guardar tarea"
        >
          <Text style={styles.botonGuardarTexto}>{guardando ? 'Guardando…' : 'Guardar tarea'}</Text>
        </Pressable>

        <Pressable
          style={styles.botonCancelar}
          onPress={onCancelar}
          testID="btn-cancelar"
          accessibilityRole="button"
          accessibilityLabel="Cancelar"
        >
          <Text style={styles.botonCancelarTexto}>Cancelar</Text>
        </Pressable>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  contenedor: { flex: 1, backgroundColor: colores.fondo },
  encabezado: {
    backgroundColor: colores.primario,
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 22,
    borderBottomLeftRadius: 24,
    borderBottomRightRadius: 24,
  },
  volver: { color: '#E0E7FF', fontSize: 15, fontWeight: '600' },
  titulo: { color: '#FFFFFF', fontSize: 26, fontWeight: '700', marginTop: 10 },
  subtitulo: { color: '#E0E7FF', fontSize: 14, marginTop: 4 },
  formulario: { padding: 16, paddingBottom: 40 },
  tarjeta: { backgroundColor: colores.superficie, borderRadius: 16, padding: 16, ...sombra },
  etiqueta: { fontSize: 14, fontWeight: '700', color: colores.texto, marginBottom: 8 },
  obligatorio: { color: colores.error },
  campo: {
    borderWidth: 1,
    borderColor: colores.borde,
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 16,
    color: colores.texto,
    backgroundColor: '#FAFAFB',
  },
  campoError: { borderColor: colores.error, backgroundColor: colores.errorSuave },
  campoMultilinea: { minHeight: 100 },
  ayuda: { fontSize: 12, color: colores.textoSecundario, marginTop: 6 },
  textoError: { fontSize: 13, color: colores.error, fontWeight: '700', marginTop: 6 },
  botonGuardar: {
    marginTop: 20,
    backgroundColor: colores.primario,
    borderRadius: 12,
    paddingVertical: 15,
    alignItems: 'center',
    ...sombra,
  },
  botonGuardarTexto: { color: '#FFFFFF', fontSize: 16, fontWeight: '700' },
  botonCancelar: { marginTop: 10, paddingVertical: 14, alignItems: 'center' },
  botonCancelarTexto: { color: colores.textoSecundario, fontSize: 15, fontWeight: '600' },
});
