export interface Tarea {
  id: string;
  titulo: string;
  descripcion: string;
  completada: boolean;
  creadaEn: string; // fecha ISO
}

export type Pantalla = 'lista' | 'nueva';
