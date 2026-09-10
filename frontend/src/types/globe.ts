export interface Coordinate {
  lat: number;
  lng: number;
}

export interface AOIBounds {
  north: number;
  south: number;
  east: number;
  west: number;
}

export interface CameraState {
  lat: number;
  lng: number;
  zoom: number;
}

export interface GlobeState {
  isRotating: boolean;
  selectedAOI: AOIBounds | null;
  camera: CameraState;
}
